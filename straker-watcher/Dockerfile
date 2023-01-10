FROM python:3.10-slim-buster
RUN apt-get update -y && \
    # We need wget to set up the PPA and xvfb to have a virtual screen and unzip to install the Chromedriver
    apt-get install -y gnupg2 wget xvfb unzip && \
    # Set up the Chrome PPA
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    # Update the package list and install chrome
    apt-get update -y && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Set up Chromedriver Environment variables
ENV CHROMEDRIVER_VERSION=104.0.5112.79 \
    CHROMEDRIVER_DIR=/chromedriver
RUN mkdir $CHROMEDRIVER_DIR && \
    # Download and install Chromedriver
    wget -q --continue -P $CHROMEDRIVER_DIR "http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" && \
    unzip $CHROMEDRIVER_DIR/chromedriver* -d $CHROMEDRIVER_DIR && \
    rm $CHROMEDRIVER_DIR/chromedriver_linux64.zip

# Put Chromedriver into the PATH
ENV TZ="Asia/Taipei" \
    PATH=$CHROMEDRIVER_DIR:$PATH

WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY ./app .
# CMD ["flask", "--app", "exchangelib_version.py", "run", "--host=0.0.0.0"]
CMD ["python3", "exchangelib_version.py"]
