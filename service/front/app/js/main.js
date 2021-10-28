/// **************************
/// Собирает данные формы
/// **************************
function getFormData($form){
    var unindexed_array = $form.serializeArray();
    var indexed_array = {};

    $.map(unindexed_array, function(n, i){
        indexed_array[n['name']] = n['value'];
    });

    return indexed_array;
}

/// **************************
/// Обработчик сабмита формы
/// **************************
$("#id_btn_submit_text").on("click", function(e) {
    var _this = $(this);
    $("#id_btn_submit_text").prop('disabled', true);
    $.ajax({
        type: "GET",
        url: config.rest_api_url + '/api/get_news',
        crossDomain: true,
        crossOrigin: true,
        cache: false,
        beforeSend: function() {
          _this
              .prop('disabled', true)
              .find('.spinner-border').removeClass('d-none');
            },
        success: function(data){
            console.log("submit success", data);
            $("#id_page_content").html("\
                  <p>Запрос выполнен
                  </p>\
            ");
        },
        error: function(data){
            console.log("submit error");
        },
        dataType: "json",
        contentType : "application/json"
    })
    .always(function(){
      // скрываем кнопку
      _this.prop('disabled', false).find('.spinner-border').addClass('d-none');
  });
});


$("#id_btn_submit_url").on("click", function(e) {
    var _this = $(this);
    $("#id_btn_submit_url").prop('disabled', true);
    $.ajax({
        type: "POST",
        url: config.rest_api_url + '/eula/url',
        crossDomain: true,
        crossOrigin: true,
        cache: false,
        beforeSend: function() {
          _this
              .prop('disabled', true)
              .find('.spinner-border').removeClass('d-none');
            },

        data: JSON.stringify(getFormData($("#id_form_eula_url"))),
        success: function(data){
            console.log("submit success", data);
            $("#id_page_content").html("\
                  <p>Файл с разметкой собирается в фоне, контент появится автоматически.\
                    <br /><br />\
                    Файл доступен по ссылке:<br />\
                    <a href='"+data.doc_link+"' target='_blank'>"+data.doc_link+"</a>\
                    <br /><br />\
                    <a href='"+data.doc_link+"' class='btn btn-success btn-lg active' target='_blank' role='button' aria-pressed='true'>\
                      Открыть файл\
                    </a><br /><br />\
                    На гугл-диске собраны все подобные файлы:<br />\
                    <a href='https://drive.google.com/drive/folders/13Xi3iNmOyLR9kLmgwwjAX65Cu-tRgVIT' class='btn btn-warning btn-lg active' target='_blank' role='button' aria-pressed='true'>\
                      Открыть диск\
                    </a>\
                  </p>\
            ");
        },
        error: function(data){
            console.log("submit error");
        },
        dataType: "json",
        contentType : "application/json"
    })
    .always(function(){
      // скрываем кнопку
      _this.prop('disabled', false).find('.spinner-border').addClass('d-none');
  });
});
