#!/bin/bash

# Test requests are redirected to https
FINAL_URL=$(curl -Ls -o /dev/null -w '%{url_effective}' http://localhost)
if [ "$FINAL_URL" != "https://localhost/" ]; then
    echo "FAIL: Request for http://localhost did not redirect to https version instead to: "
    echo $FINAL_URL
    exit 1
fi
echo -n "."

FINAL_URL=$(curl -Ls -o /dev/null -w '%{url_effective}' http://localhost/help/)
if [ "$FINAL_URL" != "https://localhost/help/" ]; then
    echo "FAIL: Request for http://localhost/help/ did not redirect to https version instead to: "
    echo $FINAL_URL
    exit 1
fi
echo -n "."

# Test requests via NGINX for the Django admin area are denied
STATUS=$(curl -Ls --insecure -o /dev/null -w '%{http_code}' https://localhost/admin/)
if [ $STATUS -ne 403 ]; then
    echo "FAIL: Request for /admin/ did not raising 403 Forbidden, instead: "
    echo $STATUS
    exit 1
fi
echo -n "."

STATUS=$(curl -Ls --insecure -o /dev/null -w '%{http_code}' https://localhost/admin)
if [ $STATUS -ne 403 ]; then
    echo "FAIL: Request for /admin did not raising 403 Forbidden, instead: "
    echo $STATUS
    exit 1
fi
echo -n "."

echo ""