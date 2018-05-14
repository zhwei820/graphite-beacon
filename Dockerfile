# private

FROM 192.168.1.5:5000/python3:v3.6

# Add code

# Install application requirements
ADD ./requirements.txt /srv/
RUN pip3 install -r /srv/requirements.txt

# Add start script
ADD ./start.sh /srv/


ADD ./graphite_beacon /srv/graphite_beacon

# Create beacon user, will own the beacon app
RUN adduser --no-create-home --disabled-login --group --system beacon
RUN chown -R beacon:beacon /srv/graphite_beacon

WORKDIR /srv

# Execute start script
CMD ["/bin/bash /srv/start.sh"]
