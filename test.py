import subprocess

def parse_playlist(playlist):
    song_list = [line[2:] for line in playlist.split("\n")]
    return song_list

def download_song(song):
    song = song.replace('"', '').replace("by ", "")
    string = f'soulseek download "{song}" -d "D:\\Dropbox (Personal)\\Music"'
    print(string)
    process = subprocess.Popen(string, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"Attempting download of {song}...")
    output, error = process.communicate(input="\n")  # Simulate pressing Enter
    if process.returncode == 0:
        print(f"Downloaded {song}: {output}")
    else:
        print(f"Failed to download {song}: {error}")

def download_playlist(song_list):
    for song in song_list:
        download_song(song)

def main():
    pstring = '- "Stayin Alive" by Bee Gees \n- "Funky Town" by Lipps Inc. \n- "Le Freak" by Chic \n- "Get Down On It" by Kool & The Gang \n- "Dont Stop Til You Get Enough" by Michael Jackson \n- "I Will Survive" by Gloria Gaynor \n- "Super Freak" by Rick James \n- "Boogie Wonderland" by Earth, Wind & Fire'

    play_list = parse_playlist(pstring)
    download_playlist(play_list)

if __name__ == "__main__":
    main()