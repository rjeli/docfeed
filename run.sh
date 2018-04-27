#!/bin/bash

docker run -v "$HOME/pdfs":"/pdfs" -p 5000:5000 docfeed
