from flask_wtf import FlaskForm


class Form(FlaskForm):
    def validate(self):
        return 'option' in self.data and self.data['option']
