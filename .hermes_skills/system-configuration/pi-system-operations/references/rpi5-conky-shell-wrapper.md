# RPi5 /usr/bin/conky Is a Shell Wrapper

## Detection
```bash
file /usr/bin/conky
# Output: /usr/bin/conky: POSIX shell script text executable  (NOT ELF!)

ls -la /usr/bin/conky.real
# Output: No such file or directory → conky silently fails with "can't open display"
```

## The Real Binary
`/usr/bin/conky.bin` (the actual ELF executable)

## Fix — Shell Wrapper at /usr/bin/conky
```bash
sudo bash -c 'cat > /usr/bin/conky << '"'"'EOF'"'"'
#!/bin/bash
DISPLAY=:0 exec /usr/bin/conky.bin "$@"
EOF
sudo chmod +x /usr/bin/conky'
```

## Also Fix CM2 Desktop File (hardcodes :1)
```bash
mkdir -p ~/.local/share/applications/
cp /usr/share/applications/conky-manager2.desktop ~/.local/share/applications/
sed -i 's/DISPLAY=:1/DISPLAY=:0/g' ~/.local/share/applications/conky-manager2.desktop
update-desktop-database ~/.local/share/applications/
```

## LXDE Autostart (RPD Session)
```bash
mkdir -p ~/.config/lxsession/rpd-x/
cat > ~/.config/lxsession/rpd-x/autostart << 'EOF'
@sh /home/Evan/.conky/conky-startup.sh
EOF
```

## Recovery If You Accidentally Overwrite /usr/bin/conky
```bash
sudo dpkg -x /var/cache/apt/archives/conky-all_*.deb /tmp/conky-pkg/
sudo cp /tmp/conky-pkg/usr/bin/conky /usr/bin/conky
```
