Slack notifications
===================

To get a slack notification you'll need to add the "Incoming Webhook" to your
account. You'll be given a URL that looks like this::

    https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX

Treat this URL as one of your application secrets.

.. class:: SlackNotification

    You can send a notification from the workspace::

        script = workspace.add_slack_notification(
            webhook="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
            channel="#touchdown",
            text="Hello from touchdown",
        )

    .. attribute:: webhook

        A ``hooks.slack.com`` url to post notifications to.

    .. attribute:: username

        The username of the bot that posts this in the channel. Messages will
        appear to come from this user, even if there isn't a user with this
        name. The default user is ``yaybu``.

    .. attribute:: icon_url

        A url to fetch an avatar from for this bot user.

    .. attribute:: icon_emoji

        A slack emoji to use as an avatar, for example ``:ghost:``. Should not
        be used at the same time as ``icon_url``.

    .. attribute:: channel

        The channel to post in. By default the integration will post in the
        channel defined by the hook itself. You can set it to a ``#channel`` or
        ``@user`` that you want to send notifications to.

    .. attribute:: text

        A message to send to the channel. You can use a touchdown serializer
        to set this based on other resources you have defined.

    .. attribute:: attachments

        A list of :class:`~Attachment`. These allow construction of prettier and
        more informative notifications.


Advanced notifications
----------------------

.. class:: Attachment

    .. attribute:: fallback

        The fallback message to show if the advanced notification is not shown
        (for example in mobile notifications or on IRC). This is required.

    .. attribute:: color

        An optional value that can either be one of ``good``, ``warning``,
        ``danger``, or any hex color code (eg. ``#439FE0``). This value is used
        to color the border along the left side of the message attachment.

    .. attribute:: pretext

        Optional text that appears above the message attachment block.

    .. attribute:: author_name

        Small text used to display the author's name.

    .. attribute:: author_link

        A valid URL that will hyperlink the author_name text mentioned above.
        Will only work if author_name is present.

    .. attribute:: author_icon

        A valid URL that displays a small 16x16px image to the left of the
        author_name text. Will only work if author_name is present.

    .. attribute:: title

        The title is displayed as larger, bold text near the top of a message
        attachment.

    .. attribute:: title_link

        If set, the ``title`` text will appear hyperlinked.

    .. attribute:: text

        This is the main text in a message attachment, and can contain standard
        message markup. The content will automatically collapse if it contains
        700+ characters or 5+ linebreaks, and will display a "Show more..."
        link to expand the content.

    .. attribute:: fields

        Metadata to show in a table inside the message attachment. Represented
        as a list of dictionaries::

            workspace.add_slack_notification(
                #.. snip ..
                attachments=[{
                    "fallback": "A deployment to production just completed",
                    "fields": [{
                        "title": "Environment",
                        "value": "production",
                        "short": True,
                    }]
                }]
            )

        The fields are:

        ``title``
            Shown as a bold heading above the ``value`` text. It cannot contain
            markup and will be escaped for you.
        ``value``
            The text value of the field. It may contain standard message markup
            and must be escaped as normal. May be multi-line.
        ``short``
            An optional flag indicating whether the value is short enough to be
            displayed side-by-side with other values.

    .. attribute:: image_url

        A valid URL to an image file that will be displayed inside a message
        attachment. Slack currently supports the following formats: GIF, JPEG,
        PNG, and BMP.

        Large images will be resized to a maximum width of 400px or a maximum
        height of 500px, while still maintaining the original aspect ratio.

    .. attribute:: thumb_url

        A valid URL to an image file that will be displayed as a thumbnail on
        the right side of a message attachment. Slack currently supports the
        following formats: GIF, JPEG, PNG, and BMP.

        The thumbnail's longest dimension will be scaled down to 75px while
        maintaining the aspect ratio of the image. The filesize of the image
        must also be less than 500 KB.

    .. attribute:: markdown_in

        Fields which have markdown in them that needs rendering. For example if
        ``text`` contains markdown you must do::

            workspace.add_slack_notification(
                attachments=[{
                    "text": "A deployment to ``production`` just completed",
                    "markdown_in": ["text"],
                }]
            )

Examples
--------

For a post deployment notification that includes a changelog snippet you can
do something like::

    workspace.add_slack_notification(
        webhook="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
        channel="#touchdown",
        attachments=[{
            "fallback": "Deployment of '1.3' to 'production' completed",
            "title": "Deployment by user1 completed",
            "text": "\n".join([
                "```",
                "- Added a new foobar <user1>",
                "- Fixed the frobnicator <user2>"
                "```",
            ]),
            "markdown_in": ["text"],
            "fields": [{
                "title": "Environment",
                "value": "production",
                "short": True,
            }, {
                "title": "Version",
                "value": "1.3",
                "short": True,
            }],
        }],
    )
