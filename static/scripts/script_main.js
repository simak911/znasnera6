function getTeamName(){
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('tname');
}

document.getElementById("confirm").addEventListener("click", function() {
    const teamname = getTeamName();
    const levelcode = document.getElementById("levelcode").value;
    const baseurl = window.location.origin;
    if (teamname && levelcode) {
      const url = `${baseurl}/entered?code=${levelcode}&tname=${teamname}`;
      window.open(url, "_self");
    } else {
      alert("Please fill in both team id and level code.");
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
