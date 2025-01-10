import streamlit as st
import logging
import dazbo_commons as dc
import yt_dlp
import os
import tempfile
import platform
import subprocess

from pytubefix import YouTube
import os
from datetime import datetime
import json

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

def sanitize_filename(title):
    """Create a safe filename from the video title"""
    if not title:
        return f"youtube_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # Remove invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '')
    return title[:100].strip()

def download_audio(url, output_path='downloads'):
    """
    Download audio from a YouTube video using PyTubeFix
    
    Args:
        url (str): YouTube video URL
        output_path (str): Directory to save the audio file
    """
    logger.info(f"Downloading audio from YouTube...{url}")
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        # Initialize YouTube object
        yt = YouTube(url, use_oauth=True)
        logger.info(f"Downloading from: {yt.title}")
        
        # Get the audio-only stream with the highest quality
        audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        
        if not audio_stream:
            logger.error("No audio stream found")
            return False, output_path, "No audio stream found"
        
        # Create safe filename
        safe_title = sanitize_filename(yt.title)
        
        # Download the audio
        logger.info(f"Downloading audio stream ({audio_stream.abr})")
        audio_file = audio_stream.download(output_path, filename=safe_title)
        
        # Rename to add proper extension (usually webm or mp4)
        base, _ = os.path.splitext(audio_file)
        new_file = f"{base}.{audio_stream.subtype}"
        if os.path.exists(new_file):
            os.remove(new_file)
        os.rename(audio_file, new_file)
        
        logger.info(f"Successfully downloaded audio to: {new_file}")
        return True, output_path, None
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
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

def search_youtube(query):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
            'dump_single_json': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            if 'entries' in info:
                return info['entries']
            else:
                return []
    except Exception as e:
        logger.error(f"Error searching YouTube: {e}")
        return []

def main():
    output_locn = setup_download()

    st.title("Cloud Music Collection")
    st.markdown("""
        <style>
            .download-section {
                border: 1px solid #e0e0e0;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .search-section {
                border: 1px solid #e0e0e0;
                padding: 10px;
                border-radius: 5px;
            }
            .stTextInput > div > div > input {
                border: 1px solid #e0e0e0;
                border-radius: 3px;
            }
            .stButton > button {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="download-section">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1], gap="small")
    with col1:
        youtube_url = st.text_input("Enter YouTube URL:", label_visibility="visible")
    with col2:
        if st.button("Download", key="download_button"):
            if youtube_url:
                with st.spinner("Downloading..."):
                    success, video_path, audio_path = download_audio(
                        youtube_url,
                        output_locn
                    )
                    if success:
                        st.success("Download completed successfully!")
                    else:
                        st.error(f"Error: {video_path}")
            else:
                st.error("Please enter a YouTube URL")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="search-section">', unsafe_allow_html=True)
    search_query = st.text_input("Enter search query:")

    if search_query:
        with st.spinner("Searching..."):
            search_results = search_youtube(search_query)
            if search_results:
                st.write("Search Results:")
                selected_videos = []
                col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 3, 2, 1])
                with col1:
                    st.write("No.")
                with col2:
                    st.write("Title")
                with col3:
                    st.write("ID")
                with col4:
                    st.write("URL")
                with col5:
                    st.write("Duration")
                with col6:
                    st.write("Select")
                for i, result in enumerate(search_results):
                    col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 3, 2, 1])
                    with col1:
                        st.write(f"{i+1}")
                    with col2:
                        st.write(result.get('title', 'N/A'))
                    with col3:
                        st.write(result.get('id', 'N/A'))
                    with col4:
                        st.write(result.get('url', 'N/A'))
                    with col5:
                        st.write(result.get('duration', 'N/A'))
                    with col6:
                        checkbox = st.checkbox("", key=f"checkbox_{i}")
                        if checkbox:
                            selected_videos.append(result)

                if selected_videos:
                    if st.button("Download Selected"):
                        with st.spinner("Downloading selected videos..."):
                            for video in selected_videos:
                                url = video.get('url')
                                if url:
                                    st.write(f"The url is: {url}")
                                    st.write(f"Downloading: {video.get('title', 'N/A')}")
                                    success, video_path, audio_path = download_audio(
                                        url,
                                        output_locn
                                    )
                                    if success:
                                        st.success(f"Downloaded: {video.get('title', 'N/A')}")
                                    else:
                                        st.error(f"Error downloading: {video.get('title', 'N/A')}. Error: {video_path}")
                                else:
                                    st.error(f"Error: Could not extract URL for {video.get('title', 'N/A')}")

            else:
                st.write("No results found.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    output_dir = output_locn
    
    # Option to extract audio
    extract_video = False
                
if __name__ == "__main__":
    main()
