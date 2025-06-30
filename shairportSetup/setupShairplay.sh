
echo ---------------------------
echo Installing Shairplay Server
echo ---------------------------

sleep 2

echo DO NOT RUN THIS SCRIPT WITH SUDO

sleep 3

echo Installing Dependencies...

sleep 1

cd "$HOME"

sudo apt-get update
sudo apt-get install build-essential git autoconf automake libtool -y

echo Downloading and Building ALAC Lib
sleep 2


git clone https://github.com/mikebrady/alac.git
cd alac

autoreconf -fi
./configure
make

sudo make install
sudo ldconfig

cd "$HOME"


echo Downloading and Building NQPTP
sleep 2

git clone https://github.com/mikebrady/nqptp.git
cd nqptp
autoreconf -fi
./configure --with-systemd-startup
make
sudo make install

sudo systemctl enable nqptp
sudo systemctl start nqptp

cd "$HOME"

echo Downloading and Installing Shairport Sync
sleep 2

sudo apt update
sudo apt upgrade
sudo apt install --no-install-recommends build-essential git autoconf automake libtool libpopt-dev libconfig-dev libasound2-dev avahi-daemon libavahi-client-dev libssl-dev libsoxr-dev libplist-dev libsodium-dev libavutil-dev libavcodec-dev libavformat-dev uuid-dev libgcrypt-dev xxd libmosquitto-dev


git clone https://github.com/mikebrady/shairport-sync.git
cd shairport-sync
autoreconf -fi
./configure --sysconfdir=/etc --with-alsa --with-soxr --with-avahi --with-ssl=openssl --with-systemd --with-airplay-2 --with-apple-alac --with-metadata --with-mqtt-client
make
sudo make install

sudo systemctl enable shairport-sync
sudo systemctl restart shairport-sync

echo ------------------------------
echo Done Installing Airplay Server
echo ------------------------------

sleep 3

echo Compiling Metadata Reciever 

sleep 2

cd "$HOME"

git clone https://github.com/mikebrady/shairport-sync-metadata-reader.git

cd shairport-sync-metadata-reader

autoreconf -i -f
./configure
make
sudo make install

echo Done compiling and installing metadata reader...

cd "$HOME"

wget https://raw.githubusercontent.com/ChickenNuggetsPerson/EInk-Display/refs/heads/main/shairportSetup/shairport-sync.conf

git clone https://github.com/ChickenNuggetsPerson/EInk-Display.git

echo 
echo Please copy shairport config file into /etc/shairport-sync.conf
echo Also, make sure to register .service files in the EInk-Display/shairportSetup folder