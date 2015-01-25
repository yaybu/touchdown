===========
ElastiCache
===========

.. module:: touchdown.aws.elasticache
   :synopsis: Elasticache resources

The ElastiCache service provides hosted REDIS and Memcache, with support for
read replicas and high availability.


CacheCluster
============

.. class:: CacheCluster

    .. attribute:: name

    .. attribute:: instance_class

        The kind of hardware to use, for example ``db.t1.micro``

    .. attribute:: engine

        The type of database to use, for example ``redis``

    .. attribute:: engine_version

        The version of the cache engine to run

    .. attribute:: port

        The TCP/IP port to listen on.

    .. attribute:: security_groups

        A list of :class:`~touchdown.aws.vpc.SecurityGroup` to apply to this
        instance.

    .. attribute:: availability_zone

        The preferred availability zone to start this CacheCluster in

    .. attribute:: multi_az

        Whether or not to enable mutli-availability-zone features

    .. attribute:: auto_minor_version_upgrade

        Automatically deploy cache minor server upgrades

    .. attribute:: num_cache_nodes

        The number of nodes to run in this cache cluster

    .. attribute:: subnet_group

        A :class:`~touchdown.aws.elasticache.SubnetGroup` that describes the
        subnets to start the cache cluster in.

    .. attribute:: parameter_group

    .. attribute:: apply_immediately


ReplicationGroup
================

.. class:: ReplicationGroup

    .. attribute:: name

    .. attribute:: description

    .. attribute:: primary_cluster

        A :class:`CacheCluster` resource.

    .. attribute:: automatic_failover

    .. attribute:: num_cache_clusters

    .. attribute:: instance_class

        The kind of hardware to use, for example ``db.t1.micro``

    .. attribute:: engine

        The type of database to use, for example ``redis``

    .. attribute:: engine_version

        The version of the cache engine to run

    .. attribute:: port

        The TCP/IP port to listen on.

    .. attribute:: security_groups

        A list of :class:`~touchdown.aws.vpc.SecurityGroup` to apply to this
        instance.

    .. attribute:: availability_zone

        The preferred availability zone to start this CacheCluster in

    .. attribute:: multi_az

        Whether or not to enable mutli-availability-zone features

    .. attribute:: auto_minor_version_upgrade

        Automatically deploy cache minor server upgrades

    .. attribute:: num_cache_nodes

        The number of nodes to run in this cache cluster

    .. attribute:: subnet_group

        A :class:`~touchdown.aws.elasticache.SubnetGroup` that describes the
        subnets to start the cache cluster in.

    .. attribute:: parameter_group

    .. attribute:: apply_immediately


SubnetGroup
===========

.. class:: SubnetGroup

    .. attribute:: name

    .. attribute: description

    .. attribute:: subnets

        A list of :class:`~touchdown.aws.vpc.Subnet` resources.
