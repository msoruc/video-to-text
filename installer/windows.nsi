Unicode true
!include "MUI2.nsh"
!include "x64.nsh"
!include "LogicLib.nsh"

Name "Video to Text"
OutFile "../dist/Video to Text Setup x64.exe"
InstallDir "$LOCALAPPDATA\Programs\Video to Text"
RequestExecutionLevel user
SetCompressor zlib
!define ARP "Software\Microsoft\Windows\CurrentVersion\Uninstall\LocalVideoToText"
!define MUI_ICON "../assets/VideoToText.ico"
!define MUI_UNICON "../assets/VideoToText.ico"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_FUNCTION LaunchApp
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Video to Text requires 64-bit Windows."
    Abort
  ${EndIf}
FunctionEnd

Function LaunchApp
  Exec '"$INSTDIR\runtime\pythonw.exe" -E -s -B "$INSTDIR\app\start.pyw"'
FunctionEnd

Section "Video to Text"
  SetOutPath "$INSTDIR"
  File /r "../build/windows-setup/payload/Video to Text/*"
  File "../assets/VideoToText.ico"
  SetOutPath "$INSTDIR\app"
  File "start.pyw"
  SetOutPath "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortcut "$SMPROGRAMS\Video to Text.lnk" "$INSTDIR\runtime\pythonw.exe" '-E -s -B "$INSTDIR\app\start.pyw"' "$INSTDIR\VideoToText.ico"
  WriteRegStr HKCU "${ARP}" "DisplayName" "Video to Text"
  WriteRegStr HKCU "${ARP}" "DisplayIcon" "$INSTDIR\VideoToText.ico"
  WriteRegStr HKCU "${ARP}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${ARP}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKCU "${ARP}" "NoModify" 1
  WriteRegDWORD HKCU "${ARP}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\Video to Text.lnk"
  DeleteRegKey HKCU "${ARP}"
  !include "../build/windows-setup/remove-payload.nsh"
  Delete "$INSTDIR\VideoToText.ico"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
SectionEnd
