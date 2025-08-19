from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Submit, Layout, Field
from django import forms
from my_app.models import Story, Chapter, Comment, Genre, Warning, Fandom, Profile, Reason, Report, Tag


class ProfileForm(forms.ModelForm):
    bio = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'bio-input',
            'placeholder': 'Tell us about yourself...'
        }),
    )
    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'name-input',
            'placeholder': 'What is your name...?'
        }),
    )

    class Meta:
        model = Profile
        fields = ['name', 'bio', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'About You',
                Field('name', css_class='form-control-lg'),
                Field('bio', rows=4)
            ),
            Submit('submit', 'Save Profile', css_class='btn-primary')
        )

class StoryForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'tag-input',
            'placeholder': '#fantasy #adventure...'
        }),
        help_text="Separate tags with spaces, use # prefix"
    )
    fandoms = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'fandom-input',
            'placeholder': 'Neon Genesis Evangelion, Legend of Zelda...'
        }),
        help_text="Separate fandoms with commas"
    )
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    warnings = forms.ModelMultipleChoiceField(
        queryset=Warning.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Story
        fields = ['title', 'synopsis', 'public', 'genres', 'warnings']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        if self.instance.pk:
            # Get tag names, convert to string for input field
            tag_list = []
            for tag in self.instance.tags.all():
                tag_list.append('#'+tag.name)
            self.fields['tags'].initial = ' '.join(tag_list)

            fandom_list = [fandom.name for fandom in self.instance.fandoms.all()]
            self.fields['fandoms'].initial = ', '.join(fandom_list)

        self.helper.layout = Layout(
            Fieldset(
                'Story Details',
                Field('title', css_class='form-control-lg'),
                Field('synopsis', rows=4),
                Field('public'),
            ),
            Fieldset(
                'Categories',
                Field('genres'),
                Field('warnings'),
            ),
            Fieldset(
                'Tags & Fandoms',
                Field('tags'),
                Field('fandoms'),
            ),
            Submit('submit', 'Save Story', css_class='btn-primary')
        )

    def clean_fandoms(self):
        raw = self.cleaned_data.get('fandoms', '')
        if isinstance(raw, list):
            raw = ','.join(raw)
        return [name.strip() for name in raw.split(',') if name.strip()]

    def clean_tags(self):
        raw = self.cleaned_data.get('tags', '')
        if isinstance(raw, list):
            raw = ','.join(raw)
        return [name.strip() for name in raw.split('#') if name.strip()]

    def save(self, commit=True, author = None):
        instance = super().save(commit=False)
        if author:
            instance.author = author
        if commit:
            instance.save()
            self.save_m2m()  # Save genres and warnings M2M

            instance.fandoms.clear()
            fandom_names = self.cleaned_data.get('fandoms', [])
            tag_names = self.cleaned_data.get('tags', [])


            for name in fandom_names:
                fandom, created = Fandom.objects.get_or_create(name=name)
                instance.fandoms.add(fandom)

            for name in tag_names:
                tag, created = Tag.objects.get_or_create(name=name)
                instance.tags.add(tag)


        return instance

class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 20}),
        }


class CommentForm(forms.ModelForm):
    content = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'content-input',
            'placeholder': 'Share your thoughts...',
            'rows': 5,
        }),
    )
    class Meta:
        model = Comment
        fields = ['content']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(

            Fieldset(
                'Comment',
                Field('content'),
            ),
            Submit('submit', 'Save Comment', css_class='btn-primary')
        )


class StorySearchForm(forms.Form):
    query = forms.CharField(required=False, label="Search",
                            widget=forms.TextInput(attrs={'placeholder': 'Search by title, author, tag, fandom'}))

    warnings = forms.ModelMultipleChoiceField(
        queryset=Warning.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Exclude Warnings"
    )
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Exclude Genres"
    )

class ReportForm(forms.ModelForm):

    reasons = forms.ModelMultipleChoiceField(
        queryset= Reason.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="Why do you want to report this post?"
    )

    class Meta:
        model = Report
        fields = ['reasons', 'text']
        labels = {
            'text': "",
        }
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': "Tell us why... (optional)"}),
        }

