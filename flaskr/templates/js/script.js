var mouseDownPos = null
var initTop = null
var initLeft = null
var prev_table = null
var static_holders = null
var board_title = null

window.addEventListener('load', function () {
  static_holders = document.getElementsByClassName("container")
  this.document.onmouseup = function(e) {
    handleMouseUp(e)
  }
  this.document.onmouseleave = function(e) {
    handleMouseUp(null)
  }

  const tasks = document.getElementsByClassName("board-item draggable");
	for (let i = 0; i < tasks.length; i++) {
    var task = tasks[i];
		task.onmousedown = function(e) {
      handleMouseDown(e, tasks[i])
    }
	}

  const errors = document.getElementsByClassName("flash");
  for (let i = 0; i < errors.length; i++) {
    var error = errors[i];
    setTimeout(function () {
      error.style.opacity = "0%";
      setTimeout(function () {
        error.style.display = "none";
      }, parseFloat(getComputedStyle(error)['transitionDuration'])*1000);
    }, 4000);
  }
})

const handleMouseDown = (event, data) => {
  if (event.target.tagName != "BUTTON") {
    mouseDownPos = data
    prev_table = mouseDownPos.getAttribute("group")
    width = mouseDownPos.getBoundingClientRect().width;
    initTop = mouseDownPos.getBoundingClientRect().top - parseInt(window.getComputedStyle(mouseDownPos).marginTop)
    initLeft = mouseDownPos.getBoundingClientRect().left - parseInt(window.getComputedStyle(mouseDownPos).marginLeft)
    mouseDownPos.style.position = "fixed";
    mouseDownPos.style.transition = "none";
    mouseDownPos.style.width = width + "px";
    mouseDownPos.style.zIndex = 2;
    var static = mouseDownPos.parentElement.children[1];
    static.style.position = "relative";
    static.style.height = mouseDownPos.getBoundingClientRect().height + "px";
    static.style.boxShadow = "inset 0px 1px 3px 0 rgba(0,0,0,0.2)";
    mouseDownPos.style.top = event.clientY - mouseDownPos.getBoundingClientRect().height/2;
    mouseDownPos.style.left = event.clientX - mouseDownPos.getBoundingClientRect().width/2;
    window.addEventListener("mousemove", handleDrag)
    for (let i = 0; i < static_holders.length; i++) {
      var static_holder = static_holders[i];
      static_holder.style.zIndex = 3
    }
  }
  }
  const handleDrag = (event) => {
    event.preventDefault()
    if (mouseDownPos) {
      mouseDownPos.style.top = (event.clientY - mouseDownPos.getBoundingClientRect().height/2) + "px";
      mouseDownPos.style.left = (event.clientX - mouseDownPos.getBoundingClientRect().width/2) + "px";
    }
  }
  const handleMouseUp = async (data) => {
    window.removeEventListener("mousemove", handleDrag)
    if (mouseDownPos) {
      const task_id = mouseDownPos.getAttribute("task_id")
      const board_id = mouseDownPos.getAttribute("board_id")
      console.log(board_id)
      mouseDownPos.style.transition = "0.2s ease-in-out"
      const target_table = data?.target?.getAttribute("group")
      if (target_table && target_table != prev_table) {
        data = {
          "group": target_table
        }
        return post(`{{ url_for('kanban.update_task') }}?id=${task_id}&board_id=${board_id}`, data, "POST")
      }
      else {
        for (let i = 0; i < static_holders.length; i++) {
          var static_holder = static_holders[i];
          static_holder.style.zIndex = 0
        }
        var static = mouseDownPos.parentElement.children[1];
        mouseDownPos.style.zIndex = 1;
        mouseDownPos.style.top = initTop + "px";
        mouseDownPos.style.left = initLeft + "px";
        setTimeout(function () {        
          static.style.position = "absolute";
          mouseDownPos.style.position = "revert";
          mouseDownPos.style.width = "100%";
          static.style.boxShadow = "none";
        }, parseFloat(getComputedStyle(mouseDownPos)['transitionDuration'])*1000)
      }
    }
  }
  const open_menu = () => {
    menu = document.getElementById("board-menu")
    overlay = document.getElementById("overlay")
    menu.style.display = "flex";
    overlay.style.display = "block";
    setTimeout(()=> {
      menu.style.width = "30%";
      overlay.style.opacity = "20%";
      setTimeout(() => {
        menu.children[0].style.opacity = "100%";
      }, parseFloat(getComputedStyle(overlay)['transitionDuration'])*1000);
    }, 50);
  }
  const close_menu = () => {
    menu = document.getElementById("board-menu")
    overlay = document.getElementById("overlay")
    menu.children[0].style.opacity = "0%";
    console.log(menu.children[0])
    menu.style.width = "0%";
    overlay.style.opacity = "0%";
    setTimeout(()=> {
      menu.style.display = "none";
      overlay.style.display = "none";
    }, parseFloat(getComputedStyle(overlay)['transitionDuration'])*1000);
  }
  const cancel_board = (element) => {
    element.style.display = "none";
    element.parentElement.children[1].style.display = "none"
    element.parentElement.style.width = "0%";
    setTimeout(()=> {
      element.parentElement.style.display = "none";
      var add_board = document.getElementsByClassName('add-board')[0]
      add_board.style.display = "flex";
    }, 
      parseFloat(getComputedStyle(element.parentElement)['transitionDuration'])*1000)
  }
  const add_board = (element) => {
    console.log(element)
    element.style.display = "none";
    element.parentElement.children[0].style.display = "flex";
    setTimeout(()=> {
      element.parentElement.children[0].style.width = "100%";
      setTimeout(() => {
        var submit_button = element.parentElement.children[0].getElementsByClassName('submit-button')[0]
        var cancel_button = element.parentElement.children[0].getElementsByClassName('cancel')[0]
        submit_button.style.display = "flex";
        cancel_button.style.display = "flex";
      }, 
        parseFloat(getComputedStyle(element.parentElement.children[0])['transitionDuration'])*1000)
    }, 
      parseFloat(50))
  }

  const alt_options = (element) => {
    console.log(element)
    var options = element.closest(".options").getElementsByClassName("options-menu")[0]
    if (!options.style.display || options.style.display == "none") {
      options.style.display = "flex";
      setTimeout(() => {
        options.style.opacity = "100%";
      }, 50);
    }
    else {
      options.style.opacity = "0%";
      setTimeout(() => {
        options.style.display = "none";
      }, parseFloat(getComputedStyle(options)['transitionDuration'])*1000);
    }
  }
  const rename_board = (element) => {
    var e = element.closest(".board-title").getElementsByClassName("board-name")[0]
    var rename = document.createElement('input');
    rename.setAttribute('type', 'text');
    rename.setAttribute('class', e.className);
    rename.setAttribute('value', e.innerText);
    rename.style.width = parseFloat(getComputedStyle(e)['width']) + parseFloat(getComputedStyle(e)['marginLeft']) + "px";
    e.parentNode.replaceChild(rename, e);
    rename.focus();
    rename.oninput = (e) => {
      rename.setAttribute('value', e.target.value)
    };
    board_title = e;
    alt_options(element)
    options_icon = element.closest(".options").getElementsByClassName("load-options")[0];
    options_icon.classList.remove("fa-ellipsis-h")
    options_icon.classList.add("fa-check")
    options_icon.onclick = () => {submit_rename(options_icon)}
    console.log(options_icon)
    
  }
  const submit_rename = async (element) => {
    board_name = element.closest(".board-title").getElementsByClassName("board-name")[0]?.value
    console.log(board_name)
    board_id = element.closest(".board-title").getAttribute("board_id")
    console.log(board_name, board_id)
    
    console.log(board_name, board_id)
    return post(`{{ url_for("kanban.rename_board") }}?board_id=${board_id}`, {"board_name": board_name}, "POST")
  }
  const cancel_rename = (element) => {
    console.log(element)
    options_icon = element.closest(".board-title").getElementsByClassName("load-options")[0];
    options_icon.classList.remove("fa-check")
    options_icon.classList.add("fa-ellipsis-h")
    options_icon.onclick = alt_options(options_icon)
    console.log(options_icon)

    var e = element.closest(".board-title").getElementsByClassName("board-name")[0]
    
    e.parentNode.replaceChild(board_title, e);
    console.log(board_title)
  }

  const add_user = (element) => {
    console.log(element)
    add_user_form = element.closest(".board-title").getElementsByClassName("new-user")[0]
    add_user_form.style.display = "flex";
    setTimeout(() => {
      add_user_form.style.top = "100%";
      alt_options(element)
    }, 50)
  }
  const close_add_user = (element) => {
    console.log(element)
    add_user_form = element.closest(".board-title").getElementsByClassName("new-user")[0]
    add_user_form.style.top = "-50%";
    setTimeout(() => {
      add_user_form.style.display = "none";
    }, parseFloat(getComputedStyle(add_user_form)["transitionDuration"])*1000)
  }

  const remove_user = async (element) => {
    console.log(element)
    user_id = element.closest(".user-info").getAttribute("user_id")
    board_id = element.closest(".user-info").getAttribute("board_id")
    console.log(user_id, board_id)
    data = {
      "remove_user_id": user_id
    }
    return post(`{{ url_for("kanban.remove_user") }}?board_id=${board_id}`, data, "POST")
  }

  const add_task = (element) => {
    console.log(element)
    column = element.closest(".board-column")
    column.getElementsByClassName("new-task")[0].style.display = "flex";
    setTimeout(() => {
      column.getElementsByClassName("new-task")[0].style.opacity = "100%";

    }
    , 50)
  }
  const close_add_task = (element) => {
    console.log(element)
    column = element.closest(".board-column")
    column.getElementsByClassName("new-task")[0].style.opacity = "0%";
    setTimeout(() => {
      column.getElementsByClassName("new-task")[0].style.display = "none";
    }, parseFloat(getComputedStyle(column.getElementsByClassName("new-task")[0])['transitionDuration'])*1000)
  }

  // Function is sampled from https://stackoverflow.com/questions/133925/javascript-post-request-like-a-form-submit
  function post(path, params, method='post') {
    const form = document.createElement('form');
    form.method = method;
    form.action = path;
  
    for (const key in params) {
      if (params.hasOwnProperty(key)) {
        const hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.name = key;
        hiddenField.value = params[key];
  
        form.appendChild(hiddenField);
      }
    }
  
    document.body.appendChild(form);
    form.submit();
  }

