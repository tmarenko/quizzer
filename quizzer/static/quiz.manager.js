function addQuestion() {
    var div = document.createElement('div');
    var question_index = $("[name^=question_]").length + 1;

    div.className = 'row';

    div.innerHTML = `
    <div class="list-group-item question" name="question_${question_index}">
        <div class="ignore-drag">
            <textarea type="text" name="question_text" placeholder="${locale['question_text']}"></textarea>
        </div>
        <div class="ignore-drag">
            <div class="d-flex m-2">
                <input type="radio" name="optionRadios${question_index}">
                <input type="text" name="option1" placeholder="${locale['answer_option']}1">
            </div>
            <div class="d-flex m-2">
                <input type="radio" name="optionRadios${question_index}">
                <input type="text" name="option2" placeholder="${locale['answer_option']}2">
            </div>
            <div class="d-flex m-2">
                <input type="radio" name="optionRadios${question_index}">
                <input type="text" name="option3" placeholder="${locale['answer_option']}3">
            </div>
            <div class="d-flex m-2">
                <input type="radio" name="optionRadios${question_index}">
                <input type="text" name="option4" placeholder="${locale['answer_option']}4">
            </div>
        </div>
        <button type="button" onclick="removeRow(this)" class="btn btn-outline-danger float-right ignore-drag">
            ${locale['remove']}
        </button>
    </div>
  `;

    document.getElementById('questions').appendChild(div);
    sortQuestions();
}

function removeRow(input) {
    document.getElementById('questions').removeChild(input.parentNode.parentNode);
}

function sortQuestions() {
    new Sortable(questions, {
        animation: 350,
        filter: '.ignore-drag',
        preventOnFilter: false
    });
}

$(window).on('load', function() {
    sortQuestions();
});

function saveQuiz(quiz_id) {
    var questions = {};
    $("#questions >> [name^=question_]").each(function() {
        var question_text = $(this).find("[name='question_text']").val();
        var options = $(this).find("[name*=option][type='text']");
        var option_checkboxes = $(this).find("[name*=optionRadios][type='radio']");
        var options_data = {};
        options.each(function(index) {
            if ($(this).val()) {
                options_data[$(this).val()] = option_checkboxes[index].checked;
            }
        });

        questions[question_text] = options_data;
    });

    var quizName = $("#quiz-name").val();
    var quiz = {};
    quiz[quizName] = questions;
    var json_data = JSON.stringify(quiz);
    var url = (typeof(quiz_id) === 'undefined') ? "/create" : `/${quiz_id}/edit`;
    console.log(`Sending POST ${url} with JSON: ${json_data}`);

    $.ajax({
        type: "POST",
        url: url,
        contentType: 'application/json',
        async: false,
        data: json_data,
        success: function(json) {
            console.log(`Got answer from the server: ${JSON.stringify(json)}`)
            if (json["result"] === "success") {
                $(location).attr('href', json["url"])
            } else {
                $('.alert-row').remove();
                var div = document.createElement('div');
                div.className = 'alert-row';
                div.innerHTML = `<div class="alert alert-danger" style="white-space: pre-line;">${json["error"]}</div>`;
                var content = document.getElementsByClassName('content')[0];
                content.insertBefore(div, content.firstChild);
            }
        }
    });
}