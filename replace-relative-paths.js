const fs = require('fs');
const path = require('path');

const rootFolder = 'D:/official/Skreenit App/recruiter'; // 🔁 Update if needed
const assetBaseURL = 'https://auth.skreenit.com/assets';

const replacements = [
  { from: /(\.\.\/)?images\//g, to: `${assetBaseURL}/images/` },
  { from: /(\.\.\/)?css\//g, to: `${assetBaseURL}/css/` },
  { from: /(\.\.\/)?js\//g, to: `${assetBaseURL}/js/` }
];

function processFile(filePath) {
  if (filePath.endsWith('.html') || filePath.endsWith('.txt')) {
    let content = fs.readFileSync(filePath, 'utf8');
    let original = content;

    replacements.forEach(({ from, to }) => {
      content = content.replace(from, to);
    });

    if (content !== original) {
      fs.writeFileSync(filePath, content, 'utf8');
      console.log(`✅ Updated: ${filePath}`);
    }
  }
}

function scanFolder(folderPath) {
  fs.readdirSync(folderPath).forEach(item => {
    const fullPath = path.join(folderPath, item);
    const stats = fs.statSync(fullPath);

    if (stats.isDirectory()) {
      scanFolder(fullPath); // 🔁 Recurse into subfolder
    } else {
      processFile(fullPath); // 📝 Process file
    }
  });
}

scanFolder(rootFolder);
