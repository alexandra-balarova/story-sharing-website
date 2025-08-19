# Story Sharing Website

My app is a web application for reading and writing stories. 

## Usage 
You can like, comment and bookmark stories and all of these actions trigger notifications. When an author publishes a new chapter, all users who've bookmarked this story receive a notification. You may search for stories by typing the title, the author, a tag or a fandom into the search bar, and you can filter out any genres or warnings. You can also interact with comments by liking or replying to them. Both stories and comments are reportable and get taken down if the report gets resolved. To resolve a report a superuser must manually change its status in the database (/admin). The author of these posts also recieves a strike, once they get 3 strikes, their account is deactivated. You can also follow other users and view their profile, as well as edit your own profile.

To add a chapter to a story, the story must first exist, so you create the story, save it, then click edit story in the header of the story detail page, scroll down to the "Chapters" card and click "add chapter". You can choose whether the story or an individual chapter is public, if it isn't, only you can see it. A chapter is private by default, you must manually publish it through the "Edit Story" form.

Tags and Fandoms fully created by users, so you may type in any that you like. Genres and Warnings are checkboxes.

When editing your profile (click view profile -> edit profile), you can customize your name, bio and profile picture. 

All posts have a "..." Options menu where you can report them, and, if you're a superuser or you're the author, delete them.

## Installation 
Run these commands in the terminal:

>pip install django-crispy-forms crispy-bootstrap4
>pip install djangorestframework

## Running

To run this app, simply run

>python migrate.py runserver

In order to read and write or interact with posts and users, you must register or log in if you already have an account, but you may read without registering. 

I have created a superuser for you so that you may view the admin view:

>username: StefanKlikovits
password: Password123

## Tests 

Run this command:

>python manage.py test my_app




