document.getElementById("confirm").addEventListener("click", function() {
    // Get the values from the input fields
    const teamname = document.getElementById("teamname").value;
    const levelcode = document.getElementById("levelcode").value;
    const baseurl = window.location.origin;

    // Construct the URL based on the input values
    if (teamname && levelcode) {
      const url = `${baseurl}/entered?code=${levelcode}&tname=${teamname}`;
      window.open(url, "_self");  // Navigate to the constructed URL
    } else {
      alert("Please fill in both team id and level code.");
    }
  });

document.getElementById("showimg").addEventListener("click", function(){
    const teamname = document.getElementById("teamname").value;
    if (teamname) {
    url = window.location.origin + '/get-img' + `?tname=${teamname}`;
    window.open(url, "_blank");}
    else {
      alert("Please fill in your team ID.")
    }
});

document.getElementById("showhint").addEventListener("click", function(){
    const teamname = document.getElementById("teamname").value;
    if (teamname) {url = window.location.origin + '/get-hint' + `?tname=${teamname}`;
    window.open(url, "_blank");}
    else {
      alert("Please fill in your team ID.")
    }
});
