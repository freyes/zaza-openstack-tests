"""Module to setup ceph-proxy charm."""

import logging
import zaza.model as model
from zaza.utilities import juju


def setup_ceph_proxy():
    """
    Configure ceph proxy with ceph metadata.

    Fetches admin_keyring and FSID from ceph-mon and
    uses those to configure ceph-proxy.
    """
    raw_admin_keyring = model.run_on_leader(
        "ceph-mon", 'cat /etc/ceph/ceph.client.admin.keyring')["Stdout"]
    admin_keyring = [
        line for line in raw_admin_keyring.split("\n") if "key" in line
    ][0].split(' = ')[-1].rstrip()
    fsid = model.run_on_leader("ceph-mon", "leader-get fsid")["Stdout"]
    cluster_ips = model.get_app_ips("ceph-mon")

    proxy_config = {
        'auth-supported': 'cephx',
        'admin-key': admin_keyring,
        'fsid': fsid,
        'monitor-hosts': ' '.join(cluster_ips)
    }

    logging.debug('Config: {}'.format(proxy_config))

    model.set_application_config("ceph-proxy", proxy_config)

    # When ceph-fs is deployed with a relation to ceph-proxy, but ceph-proxy
    # hasn't been configured yet it may seat down waiting in
    # blocked/"'ceph-mds' missing" or waiting/"'ceph-mds' incomplete", which
    # of the states will take is unpredictable, while if it's not related it
    # will always get into blocked state, so adding the relation later allows
    # consistent runs of the functional tests.
    status = juju.get_full_juju_status()
    if 'ceph-fs' in status.applications.keys():
        model.add_relation('ceph-proxy', 'mds', 'ceph-fs:ceph-mds')
