# Copyright (c) 2009 Six Apart Ltd.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of Six Apart Ltd. nor the names of its contributors may
#   be used to endorse or promote products derived from this software without
#   specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from datetime import datetime

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

import typepadapp.models
import motion.models


class PostForm(forms.Form):
    """ Form for creating new entries.
        The form includes fields for every type of
        new post, but only requires fields for the
        user-selected post type.
    """
    # Default text field messages
    body_default_text = u''
    title_default_text = u'Title'
    url_default_text = u'http://'

    post_type = forms.CharField(widget=forms.HiddenInput())
    body = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'cols': 50, 'title':body_default_text, 'id':'compose-body', 'class':'ta'}))
    title = forms.CharField(widget=forms.TextInput(attrs={'title':title_default_text, 'id':'compose-title', 'class':'ti'}))
    url = forms.URLField(widget=forms.TextInput(attrs={'title':url_default_text, 'id':'compose-url', 'class':'ti'}))
    file = forms.FileField(widget=forms.FileInput(attrs={'name':'file', 'id':'compose-file', 'class':'fi'}))

    def is_valid(self, *args, **kwargs):
        # remove/require form fields based on the note type
        post_type = self.data.get('post_type', 'post')
        self.fields['body'].required = post_type == 'post'
        self.fields['url'].required = post_type == 'link'
        self.fields['file'].required = post_type == 'photo' or post_type == 'audio'
        self.fields['title'].required = False
        #log.debug('PostForm is_valid() fields: %s' % self.fields)
        return super(PostForm, self).is_valid(*args, **kwargs)
    
    def clean_file(self):
        # File uploads should always go directly to TypePad, NEVER through Motion form processing.
        if self.fields['file'].required:
            raise forms.ValidationError(_('An error occurred while uploading your file. Please try again.'))

    def clean_title(self):
        # Check that the title is valid.
        if self.cleaned_data['title'] == self.title_default_text:
            return ''
        return self.cleaned_data['title']

    def clean_body(self):
        # Check that the post body is valid.
        if self.cleaned_data['post_type'] == 'post':
            if self.cleaned_data['body'] == self.body_default_text:
                raise forms.ValidationError(_('This field is required.'))
        if self.cleaned_data['body'] == self.body_default_text:
            return ''
        return self.cleaned_data['body']

    def clean_url(self):
        # Check that the URL field is valid.
        if self.cleaned_data['post_type'] not in ('link', 'video'): return None
        if self.cleaned_data['url'] == self.url_default_text:
            raise forms.ValidationError(_('This field is required.'))
        return self.cleaned_data['url']

    def save(self):
        """ Create the new post and return it,
            but don't actually post it to the TypePad API.
        """
        if self.cleaned_data['post_type'] == 'link':
            post = typepadapp.models.LinkAsset()
            post.link = self.cleaned_data['url']
        elif self.cleaned_data['post_type'] == 'video':
            post = typepadapp.models.Video()
            post.link = self.cleaned_data['url']
        else:
            post = typepadapp.models.Post()

        if settings.USE_TITLES:
            post.title = self.cleaned_data['title']
        else:
            post.title = ''

        post.content = self.cleaned_data['body']
        return post


class CommentForm(forms.Form):
    """ Form for creating comments. """

    body = forms.CharField(widget=forms.Textarea(attrs={'id':'comment-text'}))

    def save(self):
        """ Create the new comment and return it,
            but don't actually post it to the TypePad API.
        """
        comment = typepadapp.models.Comment()
        comment.title = ''
        comment.content = self.cleaned_data['body']
        return comment
