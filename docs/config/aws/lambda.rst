Lambda
======

.. module:: touchdown.aws.lambda_
   :synopsis: Executing code units on AWS infrastructure without managing servers


Automatic build and deploy of python lambda zips
------------------------------------------------

In order to avoid updating lambda frequently we have 2 goals for any system that produces zips to upload:

  * Reproducible builds are important. If the Sha256 hash does not change then we don't have to upload. This is fairly straightforward with Python, unless binary ``.so`` files are involved.

  * We don't want to run the build process if nothing has changed. A build system like ``make`` can use simple timestamps to tell if your build target is older than your build sources and automatically build that parts that have changed.

We assume that you have a project with a ``setup.py`` and ``requirements.txt``. Let's write a ``Makefile``. First of all we define some directories for the build to happen in::

    src_dir=$(shell pwd)
    build_dir=$(src_dir)/build
    wheel_dir=$(src_dir)/wheelhouse
    output_wheel_dir=$(build_dir)/wheels-to-deploy
    output_tree_dir=$(build_dir)/output-tree
    output_zip=$(build_dir)/lambda.zip
    wheelhouse_stamp=$(build_dir)/wheelhouse-stamp
    staging_stamp=$(build_dir)/staging-stamp
    staging_tree_stamp=$(build_dir)/staging-tree-stamp
    build_date=$(shell git log --date=local -1 --format="@%ct")

All good make files have an ``all`` that defines which targets to build if you just run ``make``. And they declare a ``.PHONY`` target. They are targets that aren't on the file system and should always be evaluated. If ``clean`` wasn't a ``.PHONY`` then a file called ``clean`` might confuse ``make`` - it would think it was responsible for building the file called ``clean``!::

    all: $(output_zip)
    .PHONY: all clean

Our ``wheelhouse-stamp`` target will build a ``pip`` wheelhouse of all our requirements. By building wheels we precompile them. Wheels are zips that we can just extract and combine into a lambda zip. By creating a stamp file ``make`` can determine if the wheelhouse is older than the ``requirements.txt``::

    $(wheelhouse_stamp): $(src_dir)/requirements.txt
        @echo "Building wheels into wheelhouse..."
        pip wheel -q -r requirements.txt . --wheel-dir=$(wheel_dir) --find-links=$(wheel_dir)
        touch $@

With the current state of tooling it is quite hard to build wheels twice and get byte identical output. So as a workaround right now you can keep this wheelhouse between builds. But then if the versions change or a dependency is removed our wheelhouse has stuff we don't want. So we have a temporary intermediate wheelhouse. Every time we update it we delete it first. It reuses the wheels from the caching wheelhouse so is fast and allows for idempotency::

    $(staging_stamp): $(src_dir)/requirements.txt $(wheelhouse_stamp)
        @echo "Collecting wheels that match requirements..."
        rm -rf $(output_wheel_dir)
        pip wheel -q -r requirements.txt . --wheel-dir=$(output_wheel_dir) --find-links=$(wheel_dir)
        touch $@

Now we need to unpack all the wheels we have collected. This is also where you would customize the output to add in extra files. We pin the max time stamp. This is because any directories that are created will have ``$NOW`` as their timestamp and this will wreck idempotence::

    $(staging_tree_stamp): $(staging_stamp)
        rm -rf $(output_tree_dir)
        unzip -q "$(output_wheel_dir)/*.whl" -d $(output_tree_dir)
        find "$(output_tree_dir)" -newermt "$(build_date)" -print0 | xargs -0r touch --no-dereference --date="$(build_date)"
        touch $@

Finally zip everything up. ``-X`` is crucial for idempotency and avoids setting various bits of extended metadata in the zip that are not reproducible and are unused::

    $(output_zip): settings.json $(staging_tree_stamp)
        rm -f $(output_zip)
        cd $(output_tree_dir) && zip -q -X -9 -r $(output_zip) *

We need a clean rule as well to remove the stamp files and the other build artifacts::

    clean:
        rm -f $(staging_tree_stamp) $(staging_stamp) $(wheelhouse_stamp)
        rm -f $(output_zip)
        rm -rf $(output_tree_dir)

Running ``make`` will now generate your ``lambda.zip`` ready to upload. Running ``make`` again should be a no-op. This means we can use ``make -q`` to create an idempotent lambda bundle. So in your ``Touchdownfile``::

    bundle = self.workspace.add_fuselage_bundle(
        target=self.workspace.add_local()
    )

    bundle.add_execute(
        command="make",
        unless="make -q",
    )

    self.aws.add_lambda_function(
        name="myfunction",
        role=self.aws.get_role(name="myrole"),
        handler="mymodule.myfunction",
        code=bundle.add_output(name="lambda.zip"),
    )

How would do I rebuild the zip when my local source changes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your project has a folder called ``myproject`` full of ``.py`` files then you can use ``find`` to build a list of dependencies and then use those dependencies to trigger a rebuild of the wheels::

    project_files = $(shell find $(src_dir)/myproject/ -type f -name '*.py')

    $(wheelhouse_stamp): $(src_dir)/requirements.txt $(project_files)
        @echo "Building wheels into wheelhouse..."
        pip wheel -q -r requirements.txt . --wheel-dir=$(wheel_dir) --find-links=$(wheel_dir)
        touch $@

If you don't want to use ``pip`` for your project, only your requirements, you can use ``cp`` and copy your ``myproject`` folder in instead::

    project_files = $(shell find $(src_dir)/myproject/ -type f -name '*.py')

    $(staging_tree_stamp): $(staging_stamp) $(project_files)
        rm -rf $(output_tree_dir)
        unzip -q "$(output_wheel_dir)/*.whl" -d $(output_tree_dir)
        cp -a $(src_dir)/myproject $(output_tree_dir)/myproject
        find "$(output_tree_dir)" -newermt "$(build_date)" -print0 | xargs -0r touch --no-dereference --date="$(build_date)"
        touch $@


How can I copy settings into my lambda.zip?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use the fuselage file resource to generate a json file. Give an SQS queue called ``myqueue``::

    bundle.add_file(
        name="settings.json",
        contents=serializers.Json(serializers.Dict(
            AWS_SQS_URL=myqueue.get_property("QueueUrl"),
        )),
    )

    bundle.add_execute(
        command=os.path.join(os.getcwd(), "make"),
        unless=os.path.join(os.getcwd(), "make -q"),
        env={
            "PATH": os.path.join(sys.prefix, "bin") + ":/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        },
        cwd=os.getcwd(),
    )

This will ensure that the queue is created before generating the ``settings.json`` that refers to it, and then create a ``settings.json`` which can be picked up by ``make``::


    $(staging_tree_stamp): $(staging_stamp) settings.json
        rm -rf $(output_tree_dir)
        unzip -q "$(output_wheel_dir)/*.whl" -d $(output_tree_dir)
        cp $(src_dir)/settings.json $(output_tree_dir)/settings.json
        find "$(output_tree_dir)" -newermt "$(build_date)" -print0 | xargs -0r touch --no-dereference --date="$(build_date)"
        touch $@

Your lambda function can then do something like this::

    import os
    FUNCTION_DIRECTORY = os.path.dirname(__file__)
    globals().update(json.loads(open(os.path.join(FUNCTION_DIRECTORY, "settings.json"))))

And all the keys in the settings files will now be available like any other global variable.


Function
--------

.. class:: Function

    You can register a lambda function against an Amazon account resource::

        def hello_world(event, context):
            print event

        aws.add_lambda_function(
            name = 'myfunction',
            role = aws.add_role(
                name='myrole',
                #..... snip ....,
            ),
            code=hello_world,
            handler="main.hello_world",
        )

    .. attribute:: name

        The name for the function, up to 64 characters.

    .. attribute:: description

        A description for the function. This is shown in the AWS console and API but is not used by lambda itself.

    .. attribute:: role

        A :class:`~touchdown.aws.iam.Role` resource.

        The IAM role that Lambda assumes when it executes your function to access any other Amazon Web Services (AWS) resources.

    .. attribute:: code

        A Zip file as bytes.

        This can be a python callable. For example::

            def hello_world(event, context):
                print event

            aws.add_lambda_function(
                name='hello_world',
                code=hello_world,
                handler='main.hello_world'
                ...
            )

        It must take 2 arguments only - ``event`` and ``context``.

        This is intended for proof of concept demos when first starting out with lambda - there is no mechanism to ship dependencies of this function, it is literally the output of `inspect.getsource()` that is uploaded.

    .. attribute:: s3_file

        An S3 :py:class:`~touchdown.aws.s3.file.File`.

        A new version of the lambda function is published when touchdown detects that the date/time stamp of this file is newer than the last modified stamp on the lambda function.

    .. attribute:: handler

        The entry point to call.

        For the ``python2.7`` runtime with a ``shrink_image.py`` module containing a function called ``handler`` the handler would be ``shrink_image.handler``.

        For the ``node`` runtime with a ``CreateThumbnail.js`` module containing an exported function called ``handler``, the handler is ``CreateThumbnail.handler``.

        For the ``java8`` runtime, this would be something like ``package.class-name.handler`` or just ``package.class-name``.

    .. attribute:: timeout

        An integer. The number of seconds (between 1 and 300) that a lambda function is allowed to execute for before it is interrupted. The default is 3 seconds.

    .. attribute:: memory

        The amount of RAM your lambda function is given. The amount of CPU is assigned based on this as well - more RAM means more CPU is allocated.

        The default value is 128mb, which is also the minimum. Can assign up to 1536mb.

    .. attribute:: publish
