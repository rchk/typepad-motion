var settings;
settings = {
    use_dwim: false,
    upload_url: '',
    favorite_url: '',
    comments_url: '',
    render_url: '',
    comments: {
        accepted: 1,
    },
    phrase: {
        textRequired: 'Please enter some text.',
        fileRequired: 'Please select a file to post.',
        invalidFileType: 'You selected an unsupported file type.',
        errorFetchingUploadURL: 'An error occurred during submission. Please try again.'
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

    // Load more comments -- permalink page
    // bradc - feel free to move this code!
    // I just stuck it at the top so I could find it
    if ($('#more-comments').size()) {
        if (more_comments) {
            $('#more-comments').show();
            $('#more-comments').click(function() {
                $('#more-comments').hide();
                $.ajax({
                    type: "GET",
                    url: settings.comments_url,
                    data: {"asset_id": asset_id, "offset": comment_offset},
                    success: function(data){
                        $("#comments-content").append(data);
                        comment_offset += comments_per_page;
                        // No more comments?
                        if (comment_offset <= total_comments){
                            $("#more-comments").show();
                        }
                    },
                    error: function(xhr, txtStatus, errorThrown) {
                        alert('Server error: ' + xhr.status + ' -- ' + xhr.statusText);
                    }
                });
            });
        }
    }
    
    // Favorite an item
    $('.favorite-action').click(function() {
        if (user && user.is_authenticated) {
            var count = parseInt($(this).html());
            if (isNaN(count)) count = 0;

            if ($(this).hasClass('scored')) {
                action = "unfavorite";
                // decrement favorite count
                count--;
            } else {
                action = "favorite";
                // increment favorite count
                count++;
            }
            $(this).toggleClass('scored');
            if (count)
                $(this).html(count.toString());
            else
                $(this).html('&nbsp;');
            // id="favorite-6a0117a70cb0017bf60117d8ad20014cb2"
            asset_id = $(this).attr('id').split('-')[1]
            // post the favorite
            $.ajax({
                type: "POST",
                url: settings.favorite_url,
                data: {"asset_id": asset_id, "action": action},
                success: function(data){
                    // do nothing
                },
                error: function(xhr, txtStatus, errorThrown) {
                    alert('Server error: ' + xhr.status + ' -- ' + xhr.statusText);
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
        if (! settings.use_dwim ) {
            post_type = $('#compose-class').val() || 'post';
            updateEntryFields($('#entry-' + post_type));
        }

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
        var previewVisible = false;
        $('#live-preview').click(function() {
            previewVisible = !previewVisible;
            if (previewVisible) {
                updateComposePreview();
                $('#compose-preview').fadeIn(450, function() {
                    $('#live-preview').html('- hide preview');
                });
            } else {
                $('#compose-preview').fadeOut(450, function() {
                    $('#live-preview').html('+ live preview');
                });
            }
            return false;
        });

        var postPreviewTimer = null;
        $('#compose-title,#compose-body').keyup(function() {
            if (!previewVisible) return;
            if (postPreviewTimer) {
                clearTimeout(postPreviewTimer);
                postPreviewTimer = null;
            }
            postPreviewTimer = setTimeout(updateComposePreview, 500);
        });

        var urlCache = {};
        function updateComposePreview() {
            // TBD: throttle me
            var val = $('#compose-body').val();
            var title = $('#compose-title').val();
            var data = parsePost( val );
            var preview = '';
            urls_to_render = [];
            for (var i = 0; i < data.urls.length; i++) {
                var link = data.urls[i];
                if (urlCache[link]) continue;
                urls_to_render.push(link);
            }

            if ( urls_to_render.length ) {
                $.post(settings.render_url, {
                    url: urls_to_render
                }, function(str) {
                    if (str && str['response']['blocks']) {
                        for (url in str['response']['blocks'])
                            urlCache[url] = str['response']['blocks'][url];
                    }
                    renderPreview(val, title);
                }, "json");
            }
            else {
                renderPreview(val, title);
            }
        }

        var lastPreview;
        var showDown;
        function renderPreview(html, title) {
            // clear placeholders
            if (html == 'Say something...') html = '';
            if (title == 'Title')  title = '';

            // no change since last render? return
            if ( lastPreview == html + title )
                return;

            lastPreview = html + title;

            // create a showdown parser
            // if (!showDown)
            //     showDown = new Showdown.converter();

            // parse out lines from input (strips leading/trailing whitespace)
            var lines = html.split(/ *\r?\n */);

            var post_type = "post";
            // other post types: status, photo, video, audio, link

            html = '';
            var para = ''; // accumulation variable for current 'paragraph'
            var used_media = 0; // counts number of embedded objects
            var para_count = 0; // counts number of 'paragraphs'
            var media_type; // holds media type for an embedded object
            for (var i = 0; i < lines.length; i++) {
                var line = lines[i];
                if ( (line == '') && (para != '') ) {
                    para = para.replace(/\s*$/, '');
                    para = para.replace(/^\s*/, '');
                    if ( para != '' ) {
                        para_count++;
                        html += (showDown ? showDown.makeHtml( para ) : '<p>' + convertLineBreaks( para ) + '</p>') + "\n\n";
                        para = '';
                    }
                }

                var m;
                // URL recognition; playing with this algorithm. One
                // variation handles parenthesis inside the URL (like in
                // Wikipedia articles). Algorithm found here:
                // http://www.regexguru.com/2008/11/detecting-urls-in-a-block-of-text/
                // /\b(?:(?:https?|ftp|file)://|www\.|ftp\.)
                //   (?:\([-A-Z0-9+&@#/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#/%=~_|$?!:,.])*
                //   (?:\([-A-Z0-9+&@#/%=~_|$?!:,.]*\)|[A-Z0-9+&@#/%=~_|$])
                if (m = line.match(/^(https?:\/\/(?:[-a-zA-Z0-9+&@#\/%=~_|$?!:;,.])*(?:[a-zA-Z0-9+&@#\/%=~_|$]))/)) {
                    if ( para != '' ) {
                        para = para.replace(/\s*$/, '');
                        para = para.replace(/^\s*/, '');
                        if ( para != '' ) {
                            para_count++;
                            html += (showDown ? showDown.makeHtml( para ) : '<p>' + convertLineBreaks( para ) + '</p>') + "\n\n";
                            para = '';
                        }
                    }
                    if (urlCache[m[1]]) {
                        // count this as an embedded media reference
                        used_media++;
                        var block = urlCache[m[1]]['html'];
                        // assign returned media type if available
                        media_type = urlCache[m[1]]['type'];
                        // check for a caption following a link; put it in the 'caption'
                        // span if one is present, then skip over the caption line.
                        if ( (i+1 <= lines.length - 1) && (lines[i+1] != '')
                            && (( i + 1 == lines.length-1 ) || ( lines[i+2] == '' ))) {
                            if (block.match(/<span class=\"caption\">/)) {
                                block = block.replace(/<span class=\"caption\">(.*?)<\/span>/, "<span class=\"caption\">"
                                    + (showDown ? showDown.makeHtml(lines[i+1]) : escapeHTML(lines[i+1])) + "</span>");
                                i++;
                            }
                            else if (media_type == "link") {
                                // handle captions for links differently. put the
                                // caption as the linked text itself.
                                block = block.replace(/(<a[^>]+>)(.+?)<\/a>/, '$1' + lines[i+1] + '</a>')
                                i++;
                            }
                        }
                        // strip an empty caption
                        block = block.replace(/<span class=\"caption\"><\/span>/, "");
                        html += block + "\n\n";
                    } else {
                        // accumulate this line as-is
                        para += line + "\n";
                    }
                }
                else {
                    // check for an embed block
                    if ( line.match(/<object/) ) {
                        // FIXME: far too trusting right now
                        // add sanitization; whitelist checks

                        used_media++;

                        // specific media typing for youtube; this should be
                        // handled in a pluggable way
                        if (line.match(/\.?youtube\.com\//))
                            media_type = "video";
                        else
                            media_type = 'other';

                        // the 'line' here should be sanitized and safe.
                        // don't escape it
                        var block = "<div class=\"embed embed-" + media_type + "\"><span class=\"embed-inner\">"
                            + line
                            + "<span class=\"caption\"></span>"
                            + "</span></div>";
                        if ( (i+1 <= lines.length - 1) && (lines[i+1] != '')
                            && (( i + 1 == lines.length-1 ) || ( lines[i+2] == '' ))) {
                            if (block.match(/<span class=\"caption\">/)) {
                                block = block.replace(/<span class=\"caption\">(.*?)<\/span>/, "<span class=\"caption\">"
                                    + (showDown ? showDown.makeHtml(lines[i+1]) : escapeHTML(lines[i+1])) + "</span>");
                                i++;
                            }
                        }
                        block = block.replace(/<span class=\"caption\"><\/span>/, "");
                        html += block + "\n\n";
                    }
                    else {
                        // add this line to the 'para' accumulator
                        para += line + "\n";
                    }
                }
            }
            // handle any remaining content in 'para' variable
            if ( para != '' ) {
                para = para.replace(/\s*$/, '');
                para = para.replace(/^\s*/, '');
                if ( para != '' ) {
                    para_count++;
                    html += (showDown ? showDown.makeHtml( para ) : '<p>' + convertLineBreaks( para ) + '</p>') + "\n\n";
                }
            }

            // only 1 media item used? this is a media post
            if (used_media == 1) {
                // force media type to 'photo' if it is 'image'
                if (media_type == "image")
                    post_type = "photo"
                else
                    post_type = media_type;
            }

            // a blog post with 1 paragraph? nope, that's a status post.
            if ((post_type == "post") && (para_count == 1))
                post_type = "status";

            // more than 1 paragraph? looks like a blog post to me...
            if (para_count > 1)
                post_type = "post";

            // someone assigned a title to a status? nope, that's a blog post.
            if (title && (title != '') && (post_type == 'status'))
                post_type = "post";

            // meta block
            var meta = "<div class=\"asset-meta\">\n"
                + "<span class=\"byline\">\n"
                + "posted by <span class=\"vcard author\"><a href=\"#\">"
                + escapeHTML( user.name ) + "</a></span>\n"
                + "just now!</span>\n"
                + "</div>\n";

            // post icon
            var icon = "<div class=\"icon icon-" + post_type + "\"></div>";

            // userpic block
            var userpic = "<div class=\"userpic\"><a href=\"\" class=\"userpic-link\">\n"
                + "<img src=\"" + escapeHTML(user.userpic) + "\" height=\"40\" width=\"40\" alt=\"" + escapeHTML(user.name) + "\" class=\"photo\" /></a>\n</div>\n\n";

            // content block
            var content = "<div class=\"asset-content\">\n"
                + "<div class=\"asset-body\">\n"
                + (title && (title != 'Title') ? ( "<h2><a href=\"#\">" + escapeHTML(title) + "</a></h2>\n\n" ) : "")
                + html + "\n</div>\n</div>\n";

            // entire list item
            html = "<li class=\"asset action-asset hentry asset-" + post_type + "\">\n"
                + icon
                + userpic
                + content
                + meta
                + "\n</li>\n";

            // *cough*HACK*cough*. if "debug" is somewhere in block, show preformatted
            // markup so we can see what's going on
            if ( html.match(/debug/) )
                html = '<p>type: ' + post_type + '</p><pre>' + escapeHTML(html) + '</pre>';

            // assign preview to compose-preview-inner div
            $('#compose-preview-inner').html(html);
        }

        function parsePost(str) {
            var lines = str.split(/ *\r?\n */);
            var urls = [];
            for (var i = 0; i < lines.length; i++) {
                var line = lines[i];
                var m;
                // /\b(?:(?:https?|ftp|file)://|www\.|ftp\.)
                //   (?:\([-A-Z0-9+&@#/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#/%=~_|$?!:,.])*
                //   (?:\([-A-Z0-9+&@#/%=~_|$?!:,.]*\)|[A-Z0-9+&@#/%=~_|$])
                // if (m = line.match(/^(https?:\/\/(?:[-a-zA-Z0-9]+\.?)+?\/(?:[-a-zA-Z0-9+&@#\/%=~_|$?!:;,.])*(?:[a-zA-Z0-9+&@#\/%=~_|$]))/)) {
                if (m = line.match(/^(https?:\/\/(?:[-a-zA-Z0-9+&@#\/%=~_|$?!:;,.])*(?:[a-zA-Z0-9+&@#\/%=~_|$]))/)) {
                    urls.push(m[1]);
                }
            }
            return { 'urls': urls };
        }

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
                $(this).val('');
            });

            // form validation; check for required fields and valid file
            // extensions...
            if (settings.use_dwim) {
                // only one file field is present; "file"
                // determine if the file matches required extensions
                var file_name = f.file.value;
                if (file_name) {
                    if (!fileExtensionCheck(file_name, ['mp3', 'aac', 'm4a', 'gif', 'jpg', 'jpeg', 'png'])) {
                        return compose_error(settings.phrase.invalidFileType);
                    }
                    return true;
                }
            } else {
                var file_name;
                if (post_type == 'audio') {
                    file_name = f.file.value;
                    if (!file_name) {
                        return compose_error(settings.phrase.fileRequired);
                    } else if (!fileExtensionCheck(file_name, ['mp3', 'aac', 'm4a'])) {
                        return compose_error(settings.phrase.invalidFileType);
                    }
                } else if (post_type == 'photo') {
                    file_name = f.file.value;
                    if (!file_name) {
                        return compose_error(settings.phrase.fileRequired);
                    } else if (!fileExtensionCheck(file_name, ['gif', 'png', 'jpg', 'jpeg'])) {
                        return compose_error(settings.phrase.invalidFileType);
                    }
                } else if (post_type == 'post') {
                    // message body is required
                    if ($("#compose-body").val() == "") {
                        return compose_error(settings.phrase.textRequired);
                    }
                }
                // file-based posts do not use ajax no matter what
                if (file_name) {
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
            }

            if (settings.use_dwim) { // dwim and ajax go together
                // flag this as an ajax request
                $(this).ajaxSubmit({
                    target: '#response-handler',
                    beforeSubmit: beforeSubmit,
                    // ajax request is always encoded in utf-8 no matter 
                    // what charset the actual page is encoded, isn't it?
                    // file-based posts do not use ajax so the type should be ok.
                    contentType: 'application/x-www-form-urlencoded; charset=utf-8',
                    success: displayEntry
                });
                return false;
            }
            else
                return true;
        });

        function beforeSubmit(){
            $('#quickpost-error').fadeOut().remove();
            $('#spinner, #spinner-status').fadeIn('fast').css('height',$('#compose').height());
        }

        // response function
        function displayEntry(){
            if ($('#response-handler #quickpost-error').size() == 0)
                $('#form-compose').clearForm();
            // hide new entry, move to main listing.
            $('#response-handler > li').hide().insertBefore('.actions ul:first li');
            // slide to show.
            $('.actions li:first').slideDown();
            $('#spinner, #spinner-status').fadeOut();
            formFieldFocus(); // FIXME: is this necessary?
            // Initiate Entry Hover behavior
            initEntryHover();
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
                        // TODO figure out what to do with checkboxes
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

// Userpic Flyouts
// Removed in favor of titles and typepad following flyouts.
/*
    var flyOut;
    // Flyout Hover/Unhover
    $(".userpic").hover(function () {
        // Hide all with class user-info
        $('.user-info').hide();
        // Show flyout after timeout
        var userInfo = $(this).children('.user-info');
        flyOut = $.timeout(function() { $(userInfo).fadeIn(200); }, 500);
    },function () {
        // Clear flyout timeout
        $.clear(flyOut);
        // Hide flyout
        $(this).children('.user-info').fadeOut(200);
    });
    // Hide flyouts if click event in flyout
    $(".userpic *").click(function () {
        $.clear(flyOut);
        $('.user-info').fadeOut(250);
    })
*/

// Commenting
// Removed in favor of non-ajax comments.
// Currently no way to reply to a comment either.
/*
    var commentDefaultVal = $('#comment-preview-comment .comment-content div').text();
    var authorDefaultVal = $("#comment-author").attr('title');
    var authorVal = $("#comment-author").val();
    var emailVal = $("#comment-email").val();
    var urlVal = $("#comment-url").val();
    if (user) {
        authorVal = user.name;
        emailVal = user.email;
        urlVal = user.url;
    }

    // set default value for Author
    $('#comment-preview-comment .author a').text(authorDefaultVal);

    // hide: comment preview, comment preview button, comment tip
    $('#comment-preview, #comment-preview-comment, #comments-open-text .tip').hide();
    // hide: all comment form labels except the last
    $('#comments-open-data label:not(:last)').hide();
    // hide: reply text
    $('.reply-comment-link').hide();
    // disable all links in comment preview
    $('#comment-preview-comment a').click(function(){ return false }); // disable links
    // show preview upon focusing on textarea of input
    $('#comments-form textarea, #comments-form input').focus(function(){
        showPreview();
    });
    // update preview comment text
    $('#comment-text').keyup(function() {
        updatePreview($(this), $('#comment-preview-comment .comment-content-inner'), commentDefaultVal);
    });
    // update preview comment author
    $('#comment-author').keyup(function() {
        updatePreview($(this), $('#comment-preview-comment .author a'), authorDefaultVal);
    });

    // If comments accepted, add reply links
    if (settings.comments.accepted)
        $('#comments-list .comment').each(function(){
            parentID = $(this).attr('id').replace("comment-", "");
            $('.byline', this).append(' | <a href="#comment-' + parentID + '" title="Reply">Reply</a>');
        });

    // Reply link click function
    $('[@title="Reply"]').click(function(){
        // add comment parent author to comment preview
        replyAuthor = $(this).parent().find('.author').html();
        $('#comment-preview-comment .reply-comment-link a span').html(replyAuthor);

        // update preview comment author
        $('#comment-author').keyup(function() {
            updatePreview($(this), $('#comment-preview-comment .author a'), authorDefaultVal);
        });

        // show comment preview reply text
        $('#comment-preview-comment .reply-comment-link').show();

        // get id from reply link
        parent_id = this.hash.replace("#comment-", "");

        // show reply form field, set focus to comment form
        mtReplyCommentOnClick(parent_id, replyAuthor);

        return false;
    });

    // toggle reply text when reply checkbox is checked
    $('#comment-reply').click(function(){ $('.reply-comment-link').toggle() });

    // Comment Submit
    $("#comment-submit").click(function(){
        // hide comment preview
        $('#comment-preview-comment').fadeOut(1000);
        // disable comment and submit button
        $("#comment-submit, #comment-text").attr("disabled","disabled");

        $("#comments-form .default-value").each(function() {
            $(this).val('');
        });

        // Get form data and post
        var staticVal = $('[name="static"]').val();
        var entryIdVal = $('[name="entry_id"]').val();
        var langVal = $('[name="lang"]').val();
        var parentIdVal = $('[name="comment_reply"]').val();
        var previewVal = $('[name="prev"]').val();
        var sidVal = $('[name="sid"]').val();
        var capthchaVal;
        var tokenVal;
        if($("#captcha_code")) {
            capthchaVal = $('#captcha_code').val();
            tokenVal = $('input[name="token"]').val();
        }
        var replyVal = $("#comment-reply").val();

        var textVal = $("#comment-text").val();
        var authorVal = $("#comment-author").val();
        var emailVal = $("#comment-email").val();
        var urlVal = $("#comment-url").val();
        if (user) {
            authorVal = user.name;
            emailVal = user.email;
            if (emailVal == undefined) emailVal = '';
            urlVal = user.url;
            if (urlVal == undefined) urlVal = '';
        }

        var postData = { static: staticVal, entry_id: entryIdVal, parent_id: parentIdVal, comment_reply: replyVal, author: authorVal, email: emailVal, url: urlVal, text: textVal, captcha_code: capthchaVal, token: tokenVal};
        $.ajax({
            type: "POST",
            url: document.location.href,
            data: postData,
            contentType: 'application/x-www-form-urlencoded; charset=utf-8',
            success: function(data){
                $("#comments-list").html(data);
                $("#comment-submit, #comment-text").removeAttr("disabled");
                if ($('#comments-list #comment-error').size() > 0) {
                    $("#comment-preview-comment").fadeIn(1000);
                } else if ($('#comments-list #comment-exclamation').size() > 0) {
                    $("#comment-text").val('');
                    $("#comment-preview-comment").fadeIn(1000);
                    mtFireEvent('commentposted', postData);
                } else {
                    $('#comment-preview-comment .comment-content-inner').html(commentDefaultVal);
                    $("#comment-text").val('');
                    mtFireEvent('commentposted', postData);
                };
            }
        });
        return false;
    });
*/

// Gallery Widget
    $("#gall-prev").click(function(){
        var gall_position = $("#photo-gallery").position();
        if (gall_position.left < 0) {
            $("#photo-gallery").animate({"left": "+=120px"}, "slow", "swing", function() {
                var gall_position_new = $("#photo-gallery").position();
                if (gall_position_new.left == 0) {
                    $("#gall-prev").addClass("disabled");
                }
            });
        }
    });
    $("#gall-next").click(function(){
        $("#photo-gallery").animate({"left": "-=120px"}, "slow");
        $("#gall-prev").removeClass("disabled");
    });


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

// Commenting Functions

var commentDefaultVal, authorDefaultVal, authorVal, emailVal, urlVal;
function updatePreviewTime(){
    $('#comment-preview-comment .byline a .published').html( $.PHPDate("M d, Y g:i A", new Date())); // set date
    // $('#comment-preview-comment .byline abbr').attr('title',$.PHPDate("c", new Date())); // set iso 8601 date (optional)
}
function showPreview(){
    var loggedin = user && user.is_authenticated;
    if (loggedin) {
        var fooname = user.name;
        $('#comment-preview-comment .byline .author a').html(fooname); // set comment author value
    } else {
        $('#comment-preview-comment .byline .author a').html(authorVal); // set comment author value
    }
    $("#comment-preview-comment, #comments-open-text .tip").fadeIn(1000); // hide comment preview
    updatePreviewTime();
}
function updatePreview(id, target, defaultVal){
    v = $(id).val();
    v = (v.length? v : defaultVal)
    v = v.replace(/\n/g, "<br />").replace(/\n\n+/g, '<br /><br />').replace(/(<\/?)script/g,"$1noscript");
    $(target).html(v);
    updatePreviewTime();
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
            if (settings.use_dwim && ($(this).attr('id') == "compose-body"))
                $('#dwim-tip').show();
        }
    // onBlur, if value empty or equal to title, add default-value class and copy value from title.
    }).bind('blur', function() {
        if ($.trim($(this).val()) == '')
            $(this).addClass('default-value').val($(this).attr('title'));
        if (settings.dwim && ($(this).attr('id') == "compose-body"))
            $('#dwim-tip').hide();
    });
}


function personalizeCommentForm() {
    if ( user && user.is_authenticated ) {
        // Set Commenter Userpic
        if (user.userpic) {
            $("#commenter-userpic").attr({
                src: user.userpic,
                alt: user.name
            });
        };
    };
}

var user = {};

$(document).bind('usersignin', showPreview);

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
