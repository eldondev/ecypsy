FROM portage
RUN emerge dev-python/pip
RUN pip install boto paramiko
ADD . /ecypsy/
