#!/bin/bash

echo "http_password: dummy" >> $TRAVIS_BUILD_DIR/secrets.yaml
echo "google_secret: dummy" >> $TRAVIS_BUILD_DIR/secrets.yaml
echo "mqtt_password: dummy" >> $TRAVIS_BUILD_DIR/secrets.yaml
echo "mqtt_username: dummy" >> $TRAVIS_BUILD_DIR/secrets.yaml
echo "ssl_key: ssl_key.pem" >> $TRAVIS_BUILD_DIR/secrets.yaml
echo "ssl_cert: ssl_cert.pem" >> $TRAVIS_BUILD_DIR/secrets.yaml
echo "db_url: dummy" >> $TRAVIS_BUILD_DIR/secrets.yaml
touch "ssl_key.pem"
touch "ssl_cert.pem"
