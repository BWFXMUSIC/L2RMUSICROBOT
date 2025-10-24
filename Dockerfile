# ✅ Use stable Python + NodeJS base image
FROM nikolaik/python-nodejs:python3.10-nodejs19

# ✅ Fix old Debian repositories and install system packages
RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list && \
    sed -i '/security.debian.org/d' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg aria2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ✅ Set working directory
WORKDIR /app

# ✅ Copy project files
COPY . .

# ✅ Upgrade pip and install dependencies
RUN python -m pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# ✅ Ensure latest stable Pyrogram is installed (fixes Peer ID issues)
RUN pip install --upgrade pyrogram tgcrypto

# ✅ Start the bot
CMD ["bash", "start"]
