# User Management and Social Media App

This Flask-based application provides user management functionalities and includes social media features like posting, following, and commenting. The app utilizes Google Cloud services such as Cloud Datastore and Cloud Storage for storing user information and media files.

## Features

1. **User Registration and Initialization:**
   - Users can register and initialize their profiles, setting a username and profile name.
   - Initial profile setup is mandatory before accessing other features.

2. **Profile and Post Management:**
   - Users can view and manage their profiles, including updating their usernames and profile names.
   - Posting images with captions is supported.
   - User posts are displayed on the main page.

3. **Social Features:**
   - Users can follow and unfollow others.
   - Followers and following lists are available on the user's profile page.

4. **Search Functionality:**
   - Users can search for other users by profile name.

5. **Comments:**
   - Users can comment on posts.

6. **Security:**
   - Firebase Authentication is used for secure user authentication.
   - User data is stored in Google Cloud Datastore.

## Installation

1. Install required Python packages:
   ```bash
   pip install Flask google-cloud-datastore google-auth google-auth-oauthlib google-auth-httplib2 google-auth-id-token google-auth-httplib2 google-cloud-storage
   ```

2. Make sure you have the necessary credentials for Google Cloud services.

3. Set up a Firebase project for authentication and obtain the configuration.

4. Update the `local_constants.py` file with your Google Cloud project details and Firebase configuration.

5. Run the Flask app:
   ```bash
   python your_app_file.py
   ```

## Usage

1. Register and initialize your profile.
2. Explore the main page to view posts from users you follow.
3. Post images with captions to share with your followers.
4. Use the search functionality to discover other users.
5. Interact with posts by commenting.

## Endpoints

- `/`: Main page displaying user posts and profile information.
- `/init`: Initial user setup and profile initialization.
- `/upload_file`: Endpoint for uploading images and creating posts.
- `/search`: Search functionality to find users by profile name.
- `/follower`: Displaying the followers of the currently logged-in user.
- `/following`: Displaying users currently followed by the logged-in user.
- `/follow/<username>`: Endpoint for following a user.
- `/unfollow/<username>`: Endpoint for unfollowing a user.
- `/user_page/<username>`: Displaying the profile and posts of a specific user.

## Contributing

Feel free to contribute to the project by submitting bug reports, feature requests, or even pull requests. Your input is highly appreciated!

## License

This app is licensed under the [MIT License](LICENSE).
