param(
    [Parameter(Mandatory = $true)]
    [string]$input_file
)

# Verify that the input file exists
if (-not (Test-Path $input_file)) {
    Write-Host "Error: File '$input_file' not found." -ForegroundColor Red
    exit 1
}

# Ensure the downloads directory exists
if (-not (Test-Path "downloads")) {
    New-Item -ItemType Directory -Path "downloads" | Out-Null
}

# Process each line from the input file
Get-Content $input_file | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq "") { return }  # Skip blank lines

    # Prepend the URL
    $url = "https://minecraft.wiki/w/$line"

    # Create a filename by replacing all non-alphanumeric and non-underscore characters with underscores,
    # then remove any spaces
    $filename = ($line -replace '[^a-zA-Z0-9_]', '_') -replace ' ', ''
    $filepath = Join-Path "downloads" "$filename.html"

    # Check if the file exists and if its size is larger than 1KB (1024 bytes)
    if (Test-Path $filepath) {
        $filesize = (Get-Item $filepath).Length
        if ($filesize -gt 1024) {
            Write-Host "File $filepath already exists and is larger than 1KB. Skipping $url."
            return
        }
    }

    # Download the webpage
    try {
        Invoke-WebRequest -Uri $url -OutFile $filepath -UseBasicParsing -ErrorAction Stop
        Write-Host "Downloaded $url to $filepath"
    }
    catch {
        Write-Host "Failed to download $url" -ForegroundColor Yellow
    }
}

Write-Host "Finished downloading webpages from $input_file."
