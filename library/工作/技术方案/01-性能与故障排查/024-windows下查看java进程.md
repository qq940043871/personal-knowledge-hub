# windows下查看java进程

可以显示出java命令行参数，查看tomcat等应用的位置

wmic process where caption="java.exe" get processid,caption,commandline /value
