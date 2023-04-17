#!/bin/bash

# Set the Git URL
git_url="https://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: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@github.com/jina0603/custom_dealer_crawl_v2"
git clone $git_url
sudo yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl start docker
sudo docker pull aerokube/selenoid:latest
cd custom_dealer_crawl_v2/scripts/
cp create_selenoid_env.sh /root
cp start_selenoid_cron.sh /root
cd /root
exit