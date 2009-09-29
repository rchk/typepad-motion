/*
 * Copyright (c) 2009 Six Apart Ltd.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * * Redistributions of source code must retain the above copyright notice,
 *   this list of conditions and the following disclaimer.
 *
 * * Redistributions in binary form must reproduce the above copyright notice,
 *   this list of conditions and the following disclaimer in the documentation
 *   and/or other materials provided with the distribution.
 *
 * * Neither the name of Six Apart Ltd. nor the names of its contributors may
 *   be used to endorse or promote products derived from this software without
 *   specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

var settings;
settings = {
    upload_url: '',
    favorite_url: '',
    comments_url: '',
    phrase: {
        textRequired: 'Please enter some text.',
        URLRequired: 'Please enter a URL.',
        fileRequired: 'Please select a file to post.',
        invalidURL: 'Whoops! The URL entered is not valid. Please check the URL and try again.',
        invalidFileType: 'You selected an unsupported file type.',
        errorFetchingUploadURL: 'An error occurred during submission. Please try again.',
        invalidTextFormat: 'Sorry, we can\'t accept posts with <HTML> or <EMBED>. Please post in text only.',
        loading: 'Loading...',
        more: 'More'
    }
};

RegExp.escape = (function() {
    var specials = [
        '/', '.', '*', '+', '?', '|',
        '(', ')', '[', ']', '{', '}', '\\'
    ];

    var sRE = new RegExp(
        '(\\' + specials.join('|\\') + ')', 'g'
    );

    return function(text) {
        return text.replace(sRE, '\\$1');
    }
})();

function escapeHTML(str) {
    return str.replace(/&/g,'&amp;').replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
}

function convertLineBreaks(str) {
    return escapeHTML(str).replace(/\n/g, "<br />\n");
}

$(document).ready(function () {

    // Click flash to close
    $('.flash').click(function() {
        $(this).fadeOut();
    });

    // Load more comments -- permalink page
    if ($('#more-comments').size()) {
        var el = $('#more-comments');
        if (more_comments) {
            el.show();
            el.click(function() {
                el.html(settings.phrase.loading);
                el.attr("disabled", "disabled");
                $.ajax({
                    type: "GET",
                    url: settings.comments_url,
                    data: {"asset_id": asset_id, "offset": comment_offset},
                    success: function(data){
                        el.removeAttr("disabled");
                        $("#comments-content").append(data);
                        comment_offset += comments_per_page;
                        // More comments?
                        if (comment_offset <= total_comments)
                            el.html(settings.phrase.more);
                        else
                            el.hide();
                    },
                    error: function(xhr, txtStatus, errorThrown) {
                        el.removeAttr("disabled");
                        alert('Server error: ' + xhr.status + ' -- ' + xhr.statusText);
                    }
                });
            });
        }
    }

    // Favorite an item
    $('.favorite-action').click(function() {
        if (user && user.is_authenticated) {
            // don't do anything if already in progress
            if ($(this).hasClass('loading')) return false;
            // show loading graphic
            $(this).toggleClass('loading');
            // favorite or un-favorite?
            var action = $(this).hasClass('scored') ? "unfavorite" : "favorite";
            // id="favorite-6a0117a70cb0017bf60117d8ad20014cb2"
            var asset_id = $(this).attr('id').split('-')[1]
            var favitem = $(this);
            // post the favorite
            $.ajax({
                type: "POST",
                url: settings.favorite_url,
                data: {"asset_id": asset_id, "action": action},
                success: function(data){
                    // increment/decrement favorite count
                    var favcount = parseInt(favitem.html());
                    if (isNaN(favcount)) favcount = 0;
                    if (action == "favorite")
                        favcount++;
                    else
                        favcount--;
                    // update count in UI
                    if (favcount)
                        favitem.html(favcount.toString());
                    else
                        favitem.html('&nbsp;');
                    // show star status
                    favitem.toggleClass('scored');
                    favitem.toggleClass('loading');
                },
                error: function(xhr, txtStatus, errorThrown) {
                    alert('An error occurred: ' + xhr.status + ' -- ' + xhr.statusText);
                    // restore old star status
                    favitem.toggleClass('loading');
                }
            });
        }
        return false;
    });

// Utility Functions
    $('body').removeClass('noscript');
    $('textarea').addClass('ta');
    $(':text').addClass('ti');
    $(':file').addClass('fi');
    // $(':password').addClass('ti').addClass('pw');
    // $(':checkbox').addClass('cb');
    // $(':radio').addClass('fi');

    // hide messaging on click
    $('.close-me').click(function() {
        $(this).parent().hide();
        return false;
    });

    // Object Converter
    function oc(a) {var o={};for(var i=0;i<a.length;i++){o[a[i]]='';};return o;}

    // Set Field Defaults
    formFieldFocus();

    $('#entry-types li a').each(function() {
        var title = $(this).attr('title');
        $(this).prepend("<span class='hint'><span class='tip'></span>" + title + '</span>');
        $(this).attr('title', '');
    });

    // Condition to only apply rules when #compose is present
    if ($('#compose').size()) {

        function fileExtensionCheck(filename, types) {
            var ext = filename.match(/[^\.]+$/);
            if (!ext) return false;
            ext = ext.toString();
            var hash = {};
            for (var i = 0; i < types.length; i++)
                hash[types[i]] = true;
            return hash[ext.toLowerCase()];
        }

    // Entry Field Manager
        // Field types
        var fieldTypes = ['title','body','url',"file",'tags'];
        // Entry Editor
        var entryTypes = {
            "entry-post": ['title','body','tags'],
            "entry-photo": ['title','body','tags','file'],
            "entry-link": ['title','body','tags','url'],
            "entry-video": ['title','body','tags','url'],
            "entry-audio": ['title','body','tags','file']
        };
        var entryClasses = {
            "entry-link":  "link",
            "entry-photo": "photo",
            "entry-audio": "audio",
            "entry-video": "video"
        };
        function updateEntryFields(entryType, speed) {
            if (!entryType.length) return;
            var speed = (speed) ? speed : '';
            $(entryType).addClass('active').siblings().removeClass('active');
            var parentID = $(entryType).attr("id");

            var old_class = $('#compose-class').val() || 'post';
            var entryClass = entryClasses[parentID] || 'post';
            $('#compose-class').val(entryClass);
            $('#entry-fields').removeClass(old_class);
            $('#entry-fields').addClass(entryClass);

            for (var i in fieldTypes) {
                var fieldName = "#field-" + fieldTypes[i];
                if (fieldTypes[i] in oc(entryTypes[parentID])) {
                    $(fieldName).fadeIn(speed);
                    $(':input', fieldName).removeAttr('disabled');
                } else {
                    $(fieldName).hide();
                    $(':input', fieldName).attr('disabled','disabled');
                }
            }
        }
        // Enable default entry fields
        post_type = $('#compose-class').val() || 'post';
        updateEntryFields($('#entry-' + post_type));

        // Change entry fields
        $('#entry-types li a').click(function() {
            updateEntryFields($(this).parent(), 250);
            return false;
        })
        var optionsVisible = false;
        $('#more-options').click(function() {
            optionsVisible = !optionsVisible;
            if (optionsVisible) {
                $('#entry-fields-optional').slideDown(450, function() {
                    $('#more-options').html('- less options');
                });
            } else {
                $('#entry-fields-optional').slideUp(450, function() {
                    $('#more-options').html('+ more options');
                });
            }
            return false;
        });

    // Compose Submission Handler
        // Create container for new entry
        $('.actions').before('<ul id="response-handler"></ul>');
        if ($('.actions ul').size() == 0)
            $('.actions').append('<ul></ul>');

        // Create containers for status messaging
        $('#compose').append('<div id="spinner"></div><div id="spinner-status"></div>');

        // Entry Submission
        $('#form-compose').submit(function(){

            // disable the submit button
            $("#post-submit").hide();
            $("#post-submit-posting").show();

            var f = $("#form-compose").get(0);
            var post_type = f.post_type.value;

            // clear any default labels
            $("#form-compose .default-value").each(function() {
                $(this).removeClass('default-value');
                if ($.trim($(this).val()) == $(this).attr('title'))
                    $(this).val('');
            });

            // Form validation; check for required fields and valid
            // values for each post type.
            var file_name;
            var post_body = $("#compose-body").val();
            if (post_body.match(/<(html|embed)/i)) {
                // HTML and embed code not allowed in the body
                return compose_error(settings.phrase.invalidTextFormat);
            }
            if (post_type == 'post') {
                // message body is required
                if (post_body == "") {
                    return compose_error(settings.phrase.textRequired);
                }
            } else if (post_type == 'link' || post_type == 'video') {
                var url = $("#compose-url").val();
                if (url == "") {
                    return compose_error(settings.phrase.URLRequired);
                } else if (!url.match(/^https?:\/\//i)){
                    // Just check for http://
                    return compose_error(settings.phrase.invalidURL);
                }
            } else if (post_type == 'photo') {
                file_name = f.file.value;
                if (!file_name) {
                    return compose_error(settings.phrase.fileRequired);
                } else if (!fileExtensionCheck(file_name, ['gif', 'png', 'jpg', 'jpeg'])) {
                    return compose_error(settings.phrase.invalidFileType);
                }
            } else if (post_type == 'audio') {
                file_name = f.file.value;
                if (!file_name) {
                    return compose_error(settings.phrase.fileRequired);
                } else if (!fileExtensionCheck(file_name, ['mp3'])) {
                    return compose_error(settings.phrase.invalidFileType);
                }
            }
            // file-based posts do not use ajax no matter what
            if (file_name) {
                // It is possible this was unset; in this event, fail gracefully
                if (settings.upload_xhr_endpoint == '') {
                    alert("No endpoint available for uploading.");
                    return false;
                }
                // Fetch the upload URL via XHR. Submit form to returned URL in callback.
                $.ajax({
                    'type': 'GET',
                    'url': settings.upload_xhr_endpoint,
                    'success': function(data, textStatus) {
                        f.action = data.substring(8, data.length);
                        if (!f.action) {
                            return compose_error(settings.phrase.errorFetchingUploadURL);
                        }
                        // JSON object to upload
                        f.asset.value = $.toJSON({
                            //'title': file_name,
                            'content': f.body.value,
                            'objectTypes':  ['tag:api.typepad.com,2009:' + 
                                post_type.substring(0,1).toUpperCase() + post_type.substring(1)]
                        });
                        // All set, submit!
                        f.submit();
                    },
                    'error': function(xhr, status_, error) {
                        alert(settings.phrase.errorFetchingUploadURL);
                    }
                });
                // Don't submit the form just yet.
                return false;
            }
            else {
                f.action = "";
            }

            return true;
        });

        function beforeSubmit(){
            $('#quickpost-error').fadeOut().remove();
            $('#spinner, #spinner-status').fadeIn('fast').css('height',$('#compose').height());
        }
    };

    // local profile editing
    if ($('#profile-data-form').size()) {

        // Edit profile
        $('#edit-profile-link').click(function () {
            // display the save/cancel buttons
            $('#profile-data-form #profile-edit').hide();
            $('#profile-data-form #profile-buttons').show();
            // make the fields editable
            $('#profile-data-form .form-field').children('.edit').each(function (i) {
                var val = $(this).siblings('.value');
                $(this).children('input').val(val.text());
            }).show();
            $('#profile-data-form .form-field').children('.value').hide();
            return false;
        });
        
        // Cancel editing
        function cancelProfileEdit(){
            $('#profile-data-form .spinner').hide();
            $('#profile-data-form .profile-data').show();
            $('#profile-data-form #profile-buttons').hide()
            $('#profile-data-form #profile-edit').show();
            $('#profile-data-form .form-field').children('.edit').hide();
            $('#profile-data-form .form-field').children('.value').show();
            return false;
        }
        $('#profile-cancel').click(cancelProfileEdit);

        // Save profile
        $('#profile-data-form').ajaxForm({
            beforeSubmit: function () {
                $('#profile-data-form .form-field').children('.edit').hide();
                $('#profile-data-form .profile-data').hide();
                $('#profile-data-form #profile-buttons').hide();
                $('#profile-data-form .spinner').show();
                return true;
            },
            success: function (responseText, statusText)  {
                //alert('status: ' + statusText + '\n\nresponseText: \n' + responseText);
                var response = eval("(" + responseText + ")");
                if (response.status == "success"){
                    // update based on user input
                    $('#profile-data-form .form-field').children('.value').each(function (i) {
                        $(this).text($(this).siblings('.edit').children('input').val());
                        $(this).text($(this).siblings('.edit').children('select').val());
                    }).show();
                    $('#profile-data-form .spinner').hide();
                    $('#profile-data-form .profile-data').show();
                    $('#profile-data-form #profile-edit').show();
                } else {
                    alert("Please correct the errors with the following fields: " + response.data);
                    cancelProfileEdit();
                }
            }
        });
    }

    // Initiate Entry Hover behavior
    initEntryHover();
}); // End Ready Function

// Hover on Entry or actions
function initEntryHover(){
    $(".asset, .actions > ul > li").hover(function(){
            $(this).addClass('hover');
        },function(){
            $(this).removeClass('hover');
        }
    );
}

// Compose Form Errors
function compose_error(message){
    alert(message);
    // enable the submit button
    $("#post-submit-posting").hide();
    $("#post-submit").show();
    return false;
}


// Utility Functions

// Form Field Focus Functions
function formFieldFocus(){
    // Set Value and class for all text fields without value.
    $('input[type=text][value=""], textarea:empty').each(function(){
        $(this).addClass('default-value').val($(this).attr('title'));
    });
    // onFocus, if value is same as title, remove default-value class and default value.
    $("input[type=text], textarea").bind('focus', function() {
        if ($.trim($(this).val()) == $(this).attr('title')) {
            $(this).removeClass('default-value').val('');
        }
    // onBlur, if value empty or equal to title, add default-value class and copy value from title.
    }).bind('blur', function() {
        if ($.trim($(this).val()) == '')
            $(this).addClass('default-value').val($(this).attr('title'));
    });
}


var user = {};

// Browser Hacks
$(document).ready(function() {
    // if Mozilla
    if ($.browser.mozilla){
        // on unload event, clear text values so that they are not cached
        $(window).unload(function(){
            $(':text, textarea').val('');
        });
    }
});

// Debug Functions
// $(document).ready(function() {
    // Object dumper
    // $('#alpha').prepend("<pre>" + $($.browser).dump() + "</pre>");
// });
