import streamlit as st
import logging
import dazbo_commons as dc
import yt_dlp
import os
import tempfile
import platform
import subprocess

# Setup logging
APP_NAME="cloud_music"
def setup_logging():    
    logger = dc.retrieve_console_logger(APP_NAME)
    logger.setLevel(logging.DEBUG)
    logger.info("Logger initialised.")
    logger.debug("DEBUG level logging enabled.")
    return logger

# utility functions
def run_command(command):
    """Run a shell command and print its output in real-time."""
    process = subprocess.Popen(
        command, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    # Read and print the output line by line
    if process.stdout is not None:
        for line in iter(process.stdout.readline, b''):
            logger.info(line.decode().strip())
        process.stdout.close()
        
    process.wait()
    
def install_software(appname: str):
    os_name = platform.system()
    logger.info(f"Installing {appname} on {os_name}...")
    
    # Mapping operating systems to their respective installation commands
    command_map = {
        "Windows": f"winget install {appname} --silent --no-upgrade",
        "Linux": f"apt -qq -y install {appname}",
        "Darwin": f"brew install {appname}"
    }
    command = command_map.get(os_name)
    if command:
        run_command(command)
        logger.info(f"Done.")
    else:
        logger.error(f"Unsupported operating system: {os_name}")

def check_installed(app_exec: str) -> bool:    
    appname, *arg = app_exec.split()
    arg = " ".join(arg)
    logger.debug(f"Checking if {appname} is installed")
    
    try:
        output = subprocess.check_output([appname, arg], stderr=subprocess.STDOUT)
        logger.debug(f"{appname} version: {output.decode().strip()}")
        logger.debug(f"{appname} is already installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug(f"{appname} is not installed or absent from path.")
        
    return False

def download_yt_video(url, output_path, download_video=False):
        try:            
            if download_video == True:
                # Options for downloading the video
                video_opts = {
                    'format': 'best',  # Download the best quality video
                    'outtmpl': f'{output_path}/%(title)s.%(ext)s',  # Save video in output directory
                }

                # Download the video
                with yt_dlp.YoutubeDL(video_opts) as ydl:
                    logger.info("Downloading video...")
                    ydl.download([url])
            
            # Options for extracting audio and saving as MP3
            audio_opts = {
                'format': 'bestaudio',  # Download the best quality audio
                'outtmpl': f'{output_path}/%(title)s.%(ext)s',  # Save audio in output directory
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
            }
            
            # Download and extract audio
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                logger.info("Extracting and saving audio as MP3...")
                ydl.download([url])
            
            return True, output_path, None
            
        except Exception as e:        
            logger.error(f"Error processing URL '{url}'.")
            logger.debug(f"The cause was: {e}") 
            return False, str(e), None
    

logger = setup_logging()

def setup_download():
    apps = [ ("ffmpeg", "ffmpeg -version"),
            ("flac", "flac --version") ]
            
    for app_install, app_exec in apps:
        if not check_installed(app_exec):
            install_software(app_install)
    locations = dc.get_locations(APP_NAME)
    for attribute, value in vars(locations).items():
        logger.debug(f"{attribute}: {value}")
    output_locn = f"{locations.output_dir}/music_files"
    return output_locn

def main():
    output_locn = setup_download()

    st.title("Cloud Music Collection")
    st.write("Download and collect online music")
    
    # Input for YouTube URL
    youtube_url = st.text_input("Enter YouTube URL:")
    
    output_dir = output_locn
    
    # Option to extract audio
    # extract_audio = st.checkbox("Extract audio from video")
    extract_video = False
    
    if st.button("Download"):
        if not youtube_url:
            st.error("Please enter a YouTube URL")
            return
            
        with st.spinner("Processing..."):
            success, video_path, audio_path = download_yt_video(
                youtube_url, 
                output_dir, 
                extract_video
            )
            
            if success:
                st.success("Download completed successfully!")
                st.write(f"Video saved to: {video_path}")
                
                if audio_path:
                    st.write(f"Audio saved to: {audio_path}")
                    
            else:
                st.error(f"Error occurred: {video_path}")
                
if __name__ == "__main__":
    main()