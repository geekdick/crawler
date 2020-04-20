#!/bin/bash
cat > /root/adsl.bash << EOF
#!/bin/bash
/usr/sbin/adsl-stop
/usr/sbin/adsl-start
curl --insecure  https://api.common.caasdata.com/proxy/ip_adsl/${1}/31288
EOF

chmod 777 /root/adsl.bash

yum install openssl -y
yum install squid -y
yum install httpd-tools -y
touch /etc/squid/squid_passwd
chown squid /etc/squid/squid_passwd
htpasswd -b /etc/squid/squid_passwd zhaohui AHSKsxky2096

mv /etc/squid/squid.conf /etc/squid/squid.conf.bak

touch /etc/squid/squid.conf
cat > /etc/squid/squid.conf << EOF 
# Auth User
auth_param basic program /usr/lib64/squid/basic_ncsa_auth /etc/squid/squid_passwd
auth_param basic children 10
auth_param basic credentialsttl 24 hours
auth_param basic realm my test prosy

#
# Recommended minimum configuration:
#
#acl manager proto cache_object
acl auth_user proxy_auth REQUIRED
acl localhost src 127.0.0.1/32
acl to_localhost dst 127.0.0.0/8 0.0.0.0/32 ::1

# Example rule allowing access from your local networks.
# Adapt to list your (internal) IP networks from where browsing
# should be allowed
acl localnet src 10.0.0.0/8     # RFC1918 possible internal network
acl localnet src 172.16.0.0/12  # RFC1918 possible internal network
acl localnet src 192.168.0.0/16 # RFC1918 possible internal network
acl localnet src fc00::/7       # RFC 4193 local private network range
acl localnet src fe80::/10      # RFC 4291 link-local (directly plugged) machines
acl localnet src 124.65.164.210

acl SSL_ports port 443
acl Safe_ports port 80          # http
acl Safe_ports port 21          # ftp
acl Safe_ports port 443         # https
acl Safe_ports port 70          # gopherf
acl Safe_ports port 210         # wais
acl Safe_ports port 1025-65535  # unregistered ports
acl Safe_ports port 280         # http-mgmt
acl Safe_ports port 488         # gss-http
acl Safe_ports port 591         # filemaker
acl Safe_ports port 777         # multiling http
acl CONNECT method CONNECT

#增加限速功能
# acl all src 0.0.0.0/0.0.0.0 
# delay_pools 1
# delay_class 1 1
# delay_access 1 allow all
# delay_parameters 1 1500000/1500000

# Recommended minimum Access Permission configuration:
#
# Only allow cachemgr access from localhost
http_access allow auth_user
http_access allow manager

# Deny requests to certain unsafe ports
http_access deny !Safe_ports

# Deny CONNECT to other than secure SSL ports
http_access deny CONNECT !SSL_ports

# We strongly recommend the following be uncommented to protect innocent
# web applications running on the proxy server who think the only
# one who can access services on "localhost" is a local user
#http_access deny to_localhost

#
# INSERT YOUR OWN RULE(S) HERE TO ALLOW ACCESS FROM YOUR CLIENTS
#

# Example rule allowing access from your local networks.
# Adapt localnet in the ACL section to list your (internal) IP networks
# from where browsing should be allowed
http_access allow localnet
http_access allow localhost

# And finally deny all other access to this proxy
http_access allow all

# Squid normally listens to port 3128cache
http_port 31288
#visible_hostname squid.zhao
# cache_mem 64 MB
# cache_swap_low 90
# cache_swap_high 95
# cache_dir ufs /tmp/squid 100 16 256
# # cache_mem 256 MB #限制使用内存大小，目前限制为实际内存一半
# acl OverConnLimit maxconn 128 #限制每个ip的最大连接数


#access_log daemon:/var/log/squid/access.log combined
# Uncomment and adjust the following to add a disk cache directory.
#cache_dir ufs /var/spool/squid 100 16 256

# Leave coredumps in the first cache dir
coredump_dir /var/spool/squid
acl NCACHE method GET
no_cache deny NCACHE

# Add any of your own refresh_pattern entries above these.
refresh_pattern ^ftp:           1440    20%     10080
refresh_pattern ^gopher:        1440    0%      1440
refresh_pattern -i (/cgi-bin/|\?) 0     0%      0
refresh_pattern .               0       20%     4320

via off
forwarded_for off

request_header_access Via deny all
request_header_access X-Forwarded-For deny all
request_header_access X-Cache deny all
request_header_access X-Cache-Lookup deny all
request_header_access Cache-Control deny all

reply_header_access Via deny all
reply_header_access Cache-Control deny all
reply_header_access Server deny all
reply_header_access X-Squid-Error deny all
reply_header_access X-Forwarded-For deny all
reply_header_access X-Cache deny all
reply_header_access X-Cache-Lookup deny all
EOF

service squid restart

if [ ! -e /var/spool/cron/ ];then
mkdir -p /var/spool/cron/
fi

echo "*/2 * * * * /bin/bash /root/adsl.bash" > /var/spool/cron/root


