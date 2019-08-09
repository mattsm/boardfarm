import pexpect
import sys
import os

import linux

class DockerFactory(linux.LinuxDevice):
    '''
    A docker host that can spawn various types of images
    '''

    model = ('docker-factory')
    prompt = ['docker_session>']
    created_docker_network = False
    created_docker = False
    extra_devices = []
    target_cname = []

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        self.ipaddr = kwargs.pop('ipaddr', None)
        self.iface = kwargs.pop('iface', None)
        self.docker_network = kwargs.pop('docker_network', None)
        self.env = kwargs.pop('env', None)
        self.name = kwargs.pop('name')
        self.cname = self.name + '-${uniq_id}'

        if self.ipaddr is not None:
            # TOOO: we rely on correct username and key and standard port
            pexpect.spawn.__init(self, command="ssh",
                                       args=['%s' % (self.ipaddr),
                                             '-o', 'StrictHostKeyChecking=no',
                                             '-o', 'UserKnownHostsFile=/dev/null',
                                             '-o', 'ServerAliveInterval=60',
                                             '-o', 'ServerAliveCountMax=5'])
        else:
            pexpect.spawn.__init__(self, command='bash', env=self.env)
            self.ipaddr = 'localhost'

        if 'BFT_DEBUG' in os.environ:
            self.logfile_read = sys.stdout

        self.expect(pexpect.TIMEOUT, timeout=1)
        self.sendline('export PS1="docker_session>"')
        self.expect(self.prompt)
        self.sendline('echo FOO')
        self.expect_exact('echo FOO')
        self.expect(self.prompt)

        self.set_cli_size(200)

        # if these interfaces are getting created let's give them time to show up
        for i in range(10):
            self.sendline('ifconfig %s' % self.iface)
            self.expect(self.prompt)
            if 'error fetching interface information: Device not found' not in self.before:
                break

        # iface set, we need to create network
        if self.iface is not None:
            self.sendline('docker network create -d macvlan -o parent=%s -o macvlan_mode=bridge %s' % (self.iface, self.cname))
            self.expect(self.prompt)
            self.sendline('docker network ls')
            self.expect(self.prompt)
            self.created_docker_network = True


        from devices import get_device
        for target in kwargs.pop('targets'):
            target_img = target['img']
            target_type = target['type']
            target_cname = target['name'] + '-${uniq_id}'

            # TODO: check for docker image and build if needed/can
            # TODO: move default command into Dockerfile
            # TODO: list of ports to forward, http proxy port for example and ssh
            self.sendline('docker run --rm --privileged --name=%s -d -p 22 %s /usr/sbin/sshd -D' % (target_cname, target_img))
            self.expect(self.prompt)
            self.expect(pexpect.TIMEOUT, timeout=1)
            self.sendline('docker network connect %s %s' % (self.cname, target_cname))
            self.expect(self.prompt)
            assert 'Error response from daemon' not in self.before, "Failed to connect docker network"
            if self.created_docker_network == True:
                self.sendline('docker exec %s ip address flush dev eth1' % target_cname)
                self.expect(self.prompt)
            self.sendline("docker port %s | grep '22/tcp' | sed 's/.*://g'" % target_cname)
            self.expect_exact("docker port %s | grep '22/tcp' | sed 's/.*://g'" % target_cname)
            self.expect(self.prompt)
            target['port'] = self.before.strip()
            int(self.before.strip())
            self.created_docker = True

            target['ipaddr'] = self.ipaddr

            new_device = get_device(target_type, **target)
            self.extra_devices.append(new_device)

            self.target_cname.append(target_cname)


    def close(self, *args, **kwargs):
        self.clean_docker()
        self.clean_docker_network()
        return super(DockerFactory, self).close(*args, **kwargs)

    def clean_docker_network(self):
        if self.created_docker_network == True:
            self.sendline('docker network rm %s' % self.cname)
            self.expect(self.prompt)
            self.sendline('docker network ls')
            self.expect(self.prompt)

    def clean_docker(self):
        if self.created_docker == True:
            for c in self.target_cname:
                self.sendline('docker stop %s' % c)
                self.expect(self.prompt)
                self.sendline('docker rm %s'% c)
                self.expect(self.prompt)
