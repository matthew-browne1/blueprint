import subprocess
from flask import Flask, render_template, send_file, jsonify, request, url_for, redirect, flash, session, current_app
import numpy as np
import pandas as pd
import seaborn as sns
import json
import os
import sys
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from urllib.parse import parse_qs
# from pyomo_opt import Optimiser
from sqlalchemy import create_engine, text, Column, DateTime, Integer, func
from sqlalchemy.orm import Session, declarative_base
import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import urllib.parse
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import secrets
import logging
from logging.handlers import RotatingFileHandler
from pyomo.environ import *
from pyomo.opt import SolverFactory
import statsmodels as sm
from scipy.optimize import minimize
from optimiser import Optimise
from pyomo_opt import Optimiser
from io import BytesIO
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy

def generate_requirements_file(output_file='requirements.txt'):
    # Run 'pip freeze' to get a list of installed packages and their versions
    result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)
    
    # Check if the command was successful
    if result.returncode == 0:
        # Write the output to the specified file
        with open(output_file, 'w') as file:
            file.write(result.stdout)
        print(f"Requirements file '{output_file}' generated successfully.")
    else:
        print("Failed to generate the requirements file.")
