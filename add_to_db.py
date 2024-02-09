from flask import Flask, render_template, send_file, jsonify, request, url_for, redirect, flash, session
import numpy as np
import pandas as pd
import seaborn as sns
import json
import os
import sys
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from urllib.parse import parse_qs
from pyomo_opt import Optimiser
from sqlalchemy import create_engine, text, Column, DateTime, Integer
from sqlalchemy.orm import Session, declarative_base, sessionmaker
import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import urllib.parse
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import secrets
from application import User, Snapshot, UserInfo, db, add_user

azure_host = "blueprintalpha.postgres.database.azure.com"
azure_user = "bptestadmin"
azure_password = "Password!"
azure_database = "postgres" 

# Create the new PostgreSQL URI for Azure
azure_db_uri = f"postgresql://{azure_user}:{urllib.parse.quote_plus(azure_password)}@{azure_host}:5432/{azure_database}"

def add_user_data(engine):
    # Create a session to interact with the database
    Session = sessionmaker(bind=engine)
    session = Session()

    # User data to be added
    user_data = [
        {'username': 'mattbrowne1', 'password': 'password123', 'full_name': 'Matthew Browne', 'email': 'matthew.browne@retailalchemy.co.uk'},
        {'username': 'testuser', 'password': 'testpassword', 'full_name': 'John Doe', 'email': 'user2@example.com'},
    ]

    # Add user data to the User and UserInfo tables
    for data in user_data:
        new_user = User(
            username=data['username'],
            password=data['password'],  # Note: You should hash the password before saving it to the database
        )
        session.add(new_user)
        session.flush()  # Get the user ID after adding to the User table

        new_user_info = UserInfo(
            full_name=data['full_name'],
            email=data['email'],
            user_id=new_user.id  # Associate the user_info with the newly created user
        )
        session.add(new_user_info)

    # Commit the changes to the database
    session.commit()

    print("User data added to the User and UserInfo tables.")

# Run the function when the script is executed
if __name__ == "__main__":
    # Replace 'your_database_uri' with the actual URI for your database
    engine = create_engine(azure_db_uri)
    add_user_data(engine)