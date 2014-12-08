Ecypsy
========
A small tool to keep machines up using ec2 spot pricing.

Things to remember:
* Ecypsy is alpha
* Ecypsy creates its own keypairs and security zones (they are eponymous), and will wipe things from those without prejudice. Do not put things that are not toys in Ecypsy right now. Maybe don't even point it at production ec2 credentials.
* Ecypsy needs tests. If anybody has grand insights about the best tests for something that sits lightly on top of ec2, let me know. Right now I am just testing locally with my own credentials.


Ecypsy (ee-sip-see) is intended to keep a number of spot instances up across ec2 availability zones.
The goal is to pay as little as possible for spot instances, while keeping the instances geographically diverse.
Ecypsy utilizes boto to interact with the amazon api, and therefore the amazon credentials you want to use should be put in some place that boto will look for them.

Things to think about:
* Ecypsy is currently deploying coreos stable. Hack get_image_id in instances.py to change that.
* Hoping to include the following in the near future:
  1. Some sort of decent networking mesh.
  2. With the networking mesh, some sort of coordination.
    * A lot of the current orchestration tools seem overblown. What is up with that?
    * Docker seems to be adding boatloads of their platform-y stuff. There is a lot of that in coreos, too, but maybe they won't push it too hard?
    * Rocket might be worth checking out.
    * raw lxc might be worth checking out
    * rolling my own ami might be worth checking out some day.
