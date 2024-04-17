from src.youtube import fetch_youtube_video_details_from_handles, download_mp3, save_speaker_raw_diarized_audio_files

if __name__ == '__main__':
    fetch_youtube_video_details_from_handles.run()
    # extract_recommended_youtube_video_name_from_link.run()
    download_mp3.main()
    save_speaker_raw_diarized_audio_files.main()

