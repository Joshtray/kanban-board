var mouseDownPos = null
var initTop = null
var initTop2 = null
var initLeft2 = null
var prev_table = null

window.addEventListener('load', function () {
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
      handleMouseDown(e, tasks[i], table=tasks[0].parentElement.parentElement.parentElement.children[0].innerHTML)
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
    mouseDownPos.style.position = "fixed";
    mouseDownPos.style.transition = "none";
    mouseDownPos.style.width = width + "px";
    mouseDownPos.style.zIndex = 2;
    var static = mouseDownPos.parentElement.children[1]
    static.style.position = "relative"
    static.style.height = mouseDownPos.getBoundingClientRect().height + "px";
    initTop2 = mouseDownPos.getBoundingClientRect().top
    initLeft2 = mouseDownPos.getBoundingClientRect().left + mouseDownPos.style.marginLeft
    initTop = mouseDownPos.parentElement.getBoundingClientRect().y
    + mouseDownPos.parentElement.getBoundingClientRect().height
    - mouseDownPos.getBoundingClientRect().height
    mouseDownPos.style.top = event.clientY - mouseDownPos.getBoundingClientRect().height/2;
    mouseDownPos.style.left = event.clientX - mouseDownPos.getBoundingClientRect().width/2;
    window.addEventListener("mousemove", handleDrag)
    static_holders = document.getElementsByClassName("container")
    console.log(static_holders.length)
    for (let i = 0; i < static_holders.length; i++) {
      var static = static_holders[i];
      static.style.zIndex = 3
    }
  }
  }
  const handleDrag = (event) => {
    event.preventDefault()
    if (mouseDownPos) {
      mouseDownPos.style.top = (event.clientY - mouseDownPos.getBoundingClientRect().height/2) + "px"
      mouseDownPos.style.left = event.clientX - mouseDownPos.getBoundingClientRect().width/2 + "px";
    }
  }
  const handleMouseUp = async (event, data) => {
    window.removeEventListener("mousemove", handleDrag)
    if (mouseDownPos) {
      const task_id = mouseDownPos.getAttribute("task_id")
      console.log(data)
      mouseDownPos.style.transition = "0.2s ease-in-out"
      if (data) {
        console.log(data)
        target_table = data.parentElement.children[0].innerHTML
        console.log(target_table)
        if (target_table != prev_table) {
          const form = new FormData()
          form.append("group", target_table)
          
          const response = await fetch(`{{ url_for('kanban.update') }}?id=${task_id}`, {
            method: 'POST',
            body: form,
          });
          window.location.reload()
        }
        else {
          static_holders = document.getElementsByClassName("container")
          for (let i = 0; i < static_holders.length; i++) {
            var static = static_holders[i];
            static.style.zIndex = 0
          }
          mouseDownPos.style.top = initTop2 + "px"
          mouseDownPos.style.left = initLeft2 + "px";
        }
      }
      else {
        static_holders = document.getElementsByClassName("container")
        for (let i = 0; i < static_holders.length; i++) {
          var static = static_holders[i];
          static.style.zIndex = 0
        }
        mouseDownPos.style.zIndex = 1;
        mouseDownPos.style.top = initTop2 + "px";
        mouseDownPos.style.left = initLeft2 + "px";
      }
      // if (event.target.classList?.contains("checked-box")) {
      //   var newGCS = event.target.parentElement.style.gridColumn.split(' / ')[0]
      //   var initGCS = mouseDownPos.parentElement.style.gridColumn.split(' / ')[0]
  
      //   var initLeft = mouseDownPos.parentElement.getBoundingClientRect().x
  
      //   mouseDownPos.style.transition = "0.2s ease-in-out"
      //   mouseDownPos.style.left = event.target.parentElement.getBoundingClientRect().x + "px"
      //   mouseDownPos.style.top = initTop + "px"
  
      //   event.target.parentElement.children[0].style.transition = "0.2s ease-in-out"
      //   event.target.parentElement.children[0].style.position = "fixed"
      //   event.target.parentElement.children[0].style.left = initLeft + "px"
      //   setTimeout(() => {
      //     event.target.parentElement.children[0].style.transition = "none"
      //     mouseDownPos.style.transition = "none"
      //     setSelObj({...selObj, 
      //       [event.target.parentElement.dataset.index]: {...selObj[event.target.parentElement.dataset.index], 
      //         position: parseInt(initGCS)-1}, 
      //         [mouseDownPos.parentElement.dataset.index]: {...selObj[mouseDownPos.parentElement.dataset.index], 
      //           position: parseInt(newGCS)-1}})        
      //   }, 200)
              
      //   mouseDownPos.style.zIndex = 1
    }
  }
