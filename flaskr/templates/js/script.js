var mouseDownPos = null
var initTop = null
var initLeft = null
var prev_table = null
var static_holders = null

window.addEventListener('load', function () {
  static_holders = document.getElementsByClassName("container")
  this.document.onmouseup = function(e) {
    handleMouseUp(e, null)
  }
  this.document.onmouseleave = function(e) {
    handleMouseUp(e, null)
  }

  const tasks = document.getElementsByClassName("board-item draggable");
	for (let i = 0; i < tasks.length; i++) {
    var task = tasks[i];
		task.onmousedown = function(e) {
      handleMouseDown(e, tasks[i], table=tasks[i].parentElement.parentElement.parentElement.children[0].innerHTML)
    }
	}

  const tables = this.document.getElementsByClassName("container");
  for (let i = 0; i < tables.length; i++) {
    var table = tables[i];
    table.onmouseup = function(e) {
      handleMouseUp(e, tables[i])
    }
  }
})

const handleMouseDown = (event, data, table) => {
  if (event.target.tagName != "BUTTON") {
    prev_table = table
    mouseDownPos = data
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
    console.log(static_holders.length)
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
  const handleMouseUp = async (event, data) => {
    window.removeEventListener("mousemove", handleDrag)
    if (mouseDownPos) {
      console.log(event, data)
      const task_id = mouseDownPos.getAttribute("task_id")
      console.log(data)
      mouseDownPos.style.transition = "0.2s ease-in-out"
      if (data) {
        console.log(data)
        target_table = data.parentElement.children[0].innerHTML
        console.log(target_table, prev_table)
        if (target_table != prev_table) {
          const form = new FormData()
          form.append("group", target_table)
          
          const response = await fetch(`{{ url_for('kanban.update') }}?id=${task_id}`, {
            method: 'POST',
            body: form,
          });
          window.location.reload()
        }
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
          mouseDownPos = null;
        }, parseFloat(getComputedStyle(mouseDownPos)['transitionDuration'])*1000)
      }
    }
  }
