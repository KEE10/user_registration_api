from fastapi.security import HTTPBasic, HTTPBasicCredentials

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from psycopg2 import extras, sql
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

import databases
import psycopg2
import uuid
import os
import hashlib
import random


class BaseUser(BaseModel):
    id: str = None
    email: str
    created_at: datetime = None
    updated_at: datetime = None


class RegisterUser(BaseUser):
    password: str
    verified: bool = False


app = FastAPI()

security = HTTPBasic()

dbhost = os.environ.get("DB_HOST")
dbport = os.environ.get("DB_PORT")
dbname = os.environ.get("DB_NAME")
dbuser = os.environ.get("DB_USER")
dbpassword = os.environ.get("DB_PASSWORD")


@app.post("/users")
async def register_user(user: RegisterUser):
    extras.register_uuid()

    activation_code = generate_activation_code()
    now = datetime.now()
    values = (
        uuid.uuid4(),
        user.email,
        hash_password(user.password),
        now,
        now,
        user.verified,
        activation_code,
        now,
    )
    await create_user_db(values)
    await send_mail(user.email, activation_code)

    return {"message": "User created successfully"}


@app.put("/users/activate")
def activate_user(email: str, activation_code: int):
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    db_activation_code = user[-2]
    db_activation_code_created_at = user[-1]
    if db_activation_code != activation_code:
        raise HTTPException(status_code=400, detail="Invalid activation code")
    if db_activation_code_created_at < datetime.now() - timedelta(minutes=1):
        # TODO: delete row so user can retry registration or when creating user check if email already exists AND verified
        raise HTTPException(status_code=400, detail="Activation code expired")
    # update row in users table to verified
    activate_user_db(user[0])
    return {"message": "User activated!"}


@app.get("/users")
async def get_users():
    connection = psycopg2.connect(
        dbname=dbname, port=dbport, host=dbhost, user=dbuser, password=dbpassword
    )
    cursor = connection.cursor()
    query = 'SELECT * FROM "Users"'
    try:
        # cursor.execute(
        #     "DELETE FROM \"Users\" WHERE email = 'khalilelamrani2@gmail.com';"
        # )
        cursor.execute(query)
        users = cursor.fetchall()

        cursor.close()
        connection.close()

        return users
    except psycopg2.Error:
        raise HTTPException(status_code=500, detail="Unexpected error")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    return hashlib.sha256(password.encode() + salt).hexdigest()


mailuser = os.environ.get("MAIL_USERNAME")
mailpassword = os.environ.get("MAIL_PASSWORD")
mailserver = os.environ.get("MAIL_SERVER")
mailport = os.environ.get("MAIL_PORT")


async def send_mail(email: str, activation_code: int):
    # configure the MailHog server connection
    conf = ConnectionConfig(
        MAIL_USERNAME=mailuser,
        MAIL_PASSWORD=mailpassword,
        MAIL_FROM="do_not_reply@userregistrationapi.com",
        MAIL_PORT=mailport,
        MAIL_SERVER=mailserver,
        MAIL_STARTTLS=0,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=False,  # disable SSL verification
    )

    # initialize the FastMail instance
    fastmail = FastMail(conf)

    # generate code
    message = MessageSchema(
        subject="Hello from FastAPI",
        recipients=[email],
        body=f"This is a test email message with your validation code: {activation_code}",
        subtype="plain",
    )
    await fastmail.send_message(message)
    return {"message": "Email sent successfully!"}


async def create_user_db(values: set):
    connection = psycopg2.connect(
        dbname=dbname, port=dbport, host=dbhost, user=dbuser, password=dbpassword
    )
    cursor = connection.cursor()
    table_col_names = [
        "id",
        "email",
        "password",
        "created_at",
        "updated_at",
        "verified",
        "activation_code",
        "activation_code_created_at",
    ]
    col_names = sql.SQL(", ").join(sql.Identifier(n) for n in table_col_names)

    place_holders = sql.SQL(", ").join(sql.Placeholder() * len(table_col_names))

    query_base = sql.SQL(
        "INSERT INTO {table_name} ({col_names}) VALUES ({values})"
    ).format(
        table_name=sql.Identifier("Users"), col_names=col_names, values=place_holders
    )
    try:
        cursor.execute(query_base, values)

        # query = sql.SQL(
        #     'INSERT INTO "Users" (id, email, password, created_at, updated_at, verified) VALUES ({}, {}, {}, {}, {}, {})'
        # )
        # extras.register_uuid()
        # # values = (
        # #     uuid.uuid4(),
        # #     sql.Literal(user.email),
        # #     sql.Literal(user.password),
        # #     datetime.now(),
        # #     datetime.now(),
        # #     user.verified,
        # # )
        # cursor.execute(
        #     query.format(
        #         uuid.uuid4(),
        #         sql.Literal(user.email),
        #         sql.Literal(user.password),
        #         datetime.now(),
        #         datetime.now(),
        #         user.verified,
        #     )
        # )
        connection.commit()
        print(f"{cursor.rowcount} record inserted successfully")

        cursor.close()
        connection.close()

    except psycopg2.errors.UniqueViolation:
        return {"User already exists"}


def get_user_by_email(email: str):
    connection = psycopg2.connect(
        dbname=dbname, port=dbport, host=dbhost, user=dbuser, password=dbpassword
    )
    cursor = connection.cursor()
    query = 'SELECT * FROM "Users" where email = %s;'
    cursor.execute(query, (email,))
    user = cursor.fetchone()

    cursor.close()
    connection.close()
    print("this is how the madafuking db returns the row::::::::::", user)
    return user


def activate_user_db(user_id: uuid):
    connection = psycopg2.connect(
        dbname=dbname, port=dbport, host=dbhost, user=dbuser, password=dbpassword
    )
    cursor = connection.cursor()
    now = datetime.now()
    query = 'UPDATE "Users" SET verified = false, updated_at = %s WHERE email = %s;'
    cursor.execute(query, (now, user_id))
    connection.commit()

    cursor.close()
    connection.close()


def generate_activation_code():
    return random.randint(1000, 9999)
