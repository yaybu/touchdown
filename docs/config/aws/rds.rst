Relational Database Service
===========================

.. module:: touchdown.aws.rds
   :synopsis: Relational Database Service resources.


Database
--------

.. class:: Database

    .. attribute:: name

        The name of the database server instance. This must be unique within
        your account/region and is required.

    .. attribute:: db_name

        The name of a database to create in this instances.

    .. ..attribute:: allocated_storage

        The amount of storage to be allocated (in GB). This must be 5 or more,
        and less than 3072. The default is 5.

    .. ..attribute:: iops

    .. ..attribute:: instance_class

        The kind of hardware to use, for example ``db.t1.micro``

    .. ..attribute:: engine

        The type of database to use, for example ``postgres``

    .. ..attribute:: engine_version

    .. ..attribute:: license_model

    .. ..attribute:: master_username

        The username of the main client user

    .. ..attribute:: master_password

        The password of the main client user

    .. ..attribute:: security_groups

        A list of security groups to apply to this instance

    .. ..attribute:: publically_accessible

    .. ..attribute:: availability_zone

    .. ..attribute:: subnet_group

        A :class:`SubnetGroup` resource.

    .. ..attribute:: preferred_maintenance_window

    .. ..attribute:: multi_az

    .. ..attribute:: storage_type

    .. ..attribute:: allow_major_version_upgrade

    .. ..attribute:: auto_minor_version_upgrade

    .. ..attribute:: character_set_name

    .. ..attribute:: backup_retention_period

    .. ..attribute:: preferred_backup_window

    .. ..attribute:: license_model

    .. ..attribute:: port

    .. ..attribute:: paramter_group

        A :class:`ParameterGroup` resource. Not currently supported.

    .. ..attribute:: option_group

        A :class:`OptionGroup` resource. Not currently supported.

    .. ..attribute:: apply_immediately



SubnetGroup
-----------

.. class:: Database

    .. attribute:: name

    .. attribute:: description

    .. attribute:: subnets

        A list of :class:`touchdown.vpc.Subnet` resources that database nodes
        can exist in.
