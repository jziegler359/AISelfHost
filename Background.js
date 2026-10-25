const canvas = document.getElementById('myCanvas');
const ctx = canvas.getContext('2d');

canvas.style.position = 'fixed';
canvas.style.inset = '0';
canvas.style.width = '100vw';
canvas.style.height = '100vh';
canvas.style.zIndex = '0';
canvas.style.pointerEvents = 'none'; // This block of code basicly makes it so that this background can go behind the HTML

document.querySelectorAll('body > *:not(#myCanvas)').forEach(element => { // this helps to scale the background with the webpage being moved around
  element.style.position = 'relative';
  element.style.zIndex = '1';
});

function circle(x,y,r,c){
  ctx.fillStyle = c
  ctx.beginPath()
  ctx.arc(x,y,r,0,2*3.14159265358979323)
  ctx.fill()
}

function Triangle(x1, y1, x2, y2, x3, y3,c) {
  ctx.fillStyle = c
  ctx.beginPath();
  ctx.moveTo(x1, y1);     
  ctx.lineTo(x2, y2);      
  ctx.lineTo(x3, y3);      
  ctx.closePath();          
  ctx.fill();          
}

function cloud(x,y,c){
  ctx.fillStyle = c;
  circle(x,y,25)
  circle(x+30,y+5,22)
  circle(x-30,y-5,27)
  circle(x-7,y+30,20)
  circle(x+7,y-30,25)
}

function quad(x1, y1, x2, y2, x3, y3, x4, y4, c) {
  ctx.fillStyle = c;
  ctx.beginPath();
  ctx.moveTo(x1, y1);     
  ctx.lineTo(x2, y2);      
  ctx.lineTo(x3, y3);      
  ctx.lineTo(x4, y4);      
  ctx.closePath();          
  ctx.fill();          
}
cx = [0,250,600,1000,1500]
cy = [200,225,250,260,210]
sc = [1,1.5,1.25,1.75,2]
rx = [0,125,190,300,425,550,675,900,1100,1400,1500,1650,1800,1900,1990,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
ry = [0,125,190,300,425,550,675,900,1100,1400,1500,1650,1800,1900,1990,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
rs = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
//Need to make sure that these are declared outside of loop learned that the hard way 
background = 1
canTogle = 1
isMouseDown = false

window.addEventListener('mousedown', () => { isMouseDown = true; })
window.addEventListener('mouseup', () => { isMouseDown = false; }) // Needed to get mouse toggle to work

let mouseX = 0
let mouseY = 0
window.addEventListener('mousemove', (event) => {
  mouseX = event.clientX
  mouseY = event.clientY //To get mouse position
})

ctx.font = "30px Arial" // text setup

function drawBackground() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  
  ctx.fillStyle = '#BCE8FA';
  ctx.fillRect(0, 0, canvas.width, canvas.height); //Draw Background first 
  quad(1500,0,1500,100,2000,100,2000,0,"white")
  ctx.fillStyle = "#000000";
  ctx.fillText("Click to toggle background", 1530, 50);
  if (background == 1){

    //Mountains
    Triangle(0,1000,600,15,1200,1000,'#A9A9A9')
    Triangle(500,1000,1250,200,2000,1000,'#36454F')
    Triangle(-500,1000,250,75,1000,1000,'#D3D3D3')
    Triangle(1000,1000,2000,300,3000,1000,'#708090 ')

    i=0
    x=10
    y=600
  
    i=0
    while (i < 5){
      cloud(cx[i],cy[i],"#FFF")
      if (cx[i]>2000){
        cx[i]=0
        cy[i] = Math.random()*400
        sc[i] = Math.random()*2
      }
      cx[i] = cx[i]+sc[i]
      i=i+1
    } // Logic kinda breaks if resized but works great in 1080px
    //rain 

    i=0//rain
    while(i<33){
      ry[i] = ry[i] + rs[i];
      rs[i] = rs[i] + 0.1
      if(ry[i]>1000){
        ry[i] = Math.random()*1500*-1
        rx[i] = Math.random()*2000
        rs[i] = 0
      }
      circle(rx[i],ry[i],10,"blue")
      i = i + 1
    }
  }
  else if (background == 2){
    //Background 2 is the grain elevator i made
    //need to make way to swtichj backgorunds and texture grass
    circle(0,0,250,"#FFED29") // sun
    quad(0,300,2000,300,2000,1000,0,1000,"#008000") //grass
    x=0
    y=400

    quad(x,y,x,y+25,x+2000,y+25,x+2000,y,"#656565 ")
    y=y+100  //To parrelel train tracks
    quad(x,y,x,y+25,x+2000,y+25,x+2000,y,"#656565 ")
    i=0
    y=400
    while(i<20){
      quad(x,y,x+20,y,x+20,y+100,x,y+100,"#4d1515")
      x = x+100
      i = i +1
    } //Train tracks
        i=0
    while (i < 5){
      cloud(cx[i],cy[i],"#FFF")
      if (cx[i]>2000){
        cx[i]=0
        cy[i] = Math.random()*400
        sc[i] = Math.random()*2
      }
      cx[i] = cx[i]+sc[i]/2
      i=i+1
    } 
    //copy and paste cloud logic execpt slower speed 
    quad(600,800,600,350,750,350,750,800,"#7d9196 ")
    quad(750,800,750,150,1000,150,1000,800,"#7e9ca3") //Main building structures 
    quad(1000,800,1000,350,1150,350,1150,800,"#7d9196 ")

    //roofs
    Triangle(750,150,1000,150,875,50,"#000000") // center
    Triangle(600,350,750,275,750,350)//Left
    Triangle(1150,350,1000,275,1000,350)//Right

    // Okay now extras
    quad(1150,350,1225,400,1225,450,1150,400,"#462b2b")//Chute
    quad(800,800,800,600,950,600,950,800,"#000000") //Door
    quad(800,800,800,1000,950,1000,950,800,"#9B7653")
  }
  requestAnimationFrame(drawBackground);
  if(mouseX >1499 & mouseY< 100){
  if (isMouseDown){
    if (canTogle == 1){
      canTogle = 0
      if(background == 1){
        background = 2
      }else{
        background =1
      }
    }
  }else{
    canTogle = 1
  }
}
  //Now just need to make a button to toggle bbetween the 2 diffrent backgrounds 
  //also need to toogle rain eITHER KEYS or buttons
}

drawBackground();
window.addEventListener('resize', drawBackground);

