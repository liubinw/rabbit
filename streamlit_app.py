import streamlit as st
import logging
import dazbo_commons as dc
import yt_dlp

# Setup logging
APP_NAME="cloud_music"
def setup_logging():    
    logger = dc.retrieve_console_logger(APP_NAME)
    logger.setLevel(logging.DEBUG)
    logger.info("Logger initialised.")
    logger.debug("DEBUG level logging enabled.")
    return logger


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