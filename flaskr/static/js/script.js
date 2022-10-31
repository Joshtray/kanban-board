var mouseDownPos = null
var initTop = null
var initTop2 = null
var initLeft2 = null

window.addEventListener('load', function () {
	const tasks = document.getElementsByClassName("board-item draggable");
  const tables = this.document.getElementsByClassName("board-column");
	for (let i = 0; i < tasks.length; i++) {
		var task = tasks[i];
		task.onmousedown = function(e) {
				handleMouseDown(e, tasks[i])
			}
	}
  for (let i = 0; i < tables.length; i++) {
    var table = tables[i];
    table.onmouseup = function(e) {
      handleMouseUp(e, tables[i])
    }
  }
})

const handleMouseDown = (event, data) => {
	mouseDownPos = data
  width = mouseDownPos.getBoundingClientRect().width
	mouseDownPos.style.position = "fixed"
  mouseDownPos.style.width = width + "px";
	mouseDownPos.style.zIndex = 2
  var static = mouseDownPos.parentElement.children[1]
  static.style.position = "relative"
  static.style.height = mouseDownPos.getBoundingClientRect().height + "px";
	initTop2 = mouseDownPos.getBoundingClientRect().top
	initLeft2 = mouseDownPos.getBoundingClientRect().left
	initTop = mouseDownPos.parentElement.getBoundingClientRect().y
	+ mouseDownPos.parentElement.getBoundingClientRect().height
	- mouseDownPos.getBoundingClientRect().height
	mouseDownPos.style.top = event.clientY - mouseDownPos.getBoundingClientRect().height/2;
	mouseDownPos.style.left = event.clientX - mouseDownPos.getBoundingClientRect().width/2;
    window.addEventListener("mousemove", handleDrag)
  }
  const handleDrag = (event) => {
    if (mouseDownPos) {
      mouseDownPos.style.top = (event.clientY - mouseDownPos.getBoundingClientRect().height/2) + "px"
      mouseDownPos.style.left = event.clientX - mouseDownPos.getBoundingClientRect().width/2 + "px";
    }
  }
  const handleMouseUp = (event) => {
    window.removeEventListener("mousemove", handleDrag)
    if (event.target.classList.contains("checked-box") && mouseDownPos) {
      var newGCS = event.target.parentElement.style.gridColumn.split(' / ')[0]
      var initGCS = mouseDownPos.parentElement.style.gridColumn.split(' / ')[0]

      var initLeft = mouseDownPos.parentElement.getBoundingClientRect().x

      mouseDownPos.style.transition = "0.2s ease-in-out"
      mouseDownPos.style.left = event.target.parentElement.getBoundingClientRect().x + "px"
      mouseDownPos.style.top = initTop + "px"

      event.target.parentElement.children[0].style.transition = "0.2s ease-in-out"
      event.target.parentElement.children[0].style.position = "fixed"
      event.target.parentElement.children[0].style.left = initLeft + "px"
      setTimeout(() => {
        event.target.parentElement.children[0].style.transition = "none"
        mouseDownPos.style.transition = "none"
        setSelObj({...selObj, 
          [event.target.parentElement.dataset.index]: {...selObj[event.target.parentElement.dataset.index], 
            position: parseInt(initGCS)-1}, 
            [mouseDownPos.parentElement.dataset.index]: {...selObj[mouseDownPos.parentElement.dataset.index], 
              position: parseInt(newGCS)-1}})        
      }, 200)
            
      mouseDownPos.style.zIndex = 1
    }
    else if (mouseDownPos) {
      mouseDownPos.style.top = initTop2 + "px"
      mouseDownPos.style.left = initLeft2 + "px";
      mouseDownPos.style.zIndex = 1;
    }
  }