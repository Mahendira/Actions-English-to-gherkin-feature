from flask import Flask, request, render_template, redirect, url_for, flash
import boto3
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 'your_secret_key'

dynamodb = boto3.resource('dynamodb')

# Replace 'ContactSubmissions' with your actual DynamoDB table name
TABLE_NAME = 'ContactSubmissions'

def save_submission(first_name, last_name, email, message):
    table = dynamodb.Table(TABLE_NAME)
    try:
        table.put_item(
            Item={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'message': message
            }
        )
    except ClientError:
        return False
    return True

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        message = request.form.get('message')

        if not first_name:
            flash('First name is required.')
            return redirect(url_for('contact'))
        if not email or '@' not in email:
            flash('Invalid email address.')
            return redirect(url_for('contact'))

        if save_submission(first_name, last_name, email, message):
            return redirect(url_for('confirmation'))
        else:
            flash('There was a problem saving your submission. Please try again.')
            return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

if __name__ == '__main__':
    app.run(debug=True)
