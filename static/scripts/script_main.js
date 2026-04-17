let hinttimes = [];

function getTeamName(){
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('tname');
}

async function getHintTimes(){
  const baseurl = window.location.origin;
  const teamname = getTeamName();
  const url = `${baseurl}/get-hinttimes?tname=${teamname}`;
  const response = await fetch(url);
  const json = await response.json();
  const status = json.status;
  if (status == 'valid') {
    hinttimes = json.htimes;
  }
}

function showHintTimes(){
  const timestamp = Math.round(Date.now() / 1000);
  const hintcount = hinttimes.length;
  for (let i=0; i < hintcount; i++) {
    const hinttime = hinttimes[i];
    const waittime = hinttime - timestamp;
    if (waittime > 0) {
      document.getElementById("hintlabel").innerHTML = `Čas na ${i+1}. nápovědu:`;
      document.getElementById("hinttime").innerHTML = `${waittime}`;
      break;
    }
  }
}

document.getElementById("confirm").addEventListener("click", function() {
    const teamname = getTeamName();
    const levelcode = document.getElementById("levelcode").value;
    const baseurl = window.location.origin;
    if (teamname && levelcode) {
      const url = `${baseurl}/entered?code=${levelcode}&tname=${teamname}`;
      window.open(url, "_self");
    } else {
      alert("Prosím zadej heslo stanoviště.");
    }
  });

document.getElementById("showimg").addEventListener("click", function(){
    const teamname = getTeamName();
    url = window.location.origin + '/get-img' + `?tname=${teamname}`;
    window.open(url, "_blank");
});

document.getElementById("showhint").addEventListener("click", function(){
    const teamname = getTeamName();
    url = window.location.origin + '/get-hint' + `?tname=${teamname}`;
    window.open(url, "_blank");
});

getHintTimes();
setInterval(showHintTimes, 500);