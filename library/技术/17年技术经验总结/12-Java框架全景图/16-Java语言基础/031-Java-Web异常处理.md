# Java-Web异常处理

![](images/1665568968825-c71a2d70-3a3c-4953-bedd-58127950849b-c4977506.png)

首先我的action类、service类和dao类如果有必要捕获异常，我都会try...catch，catch块内不记录log，通常是抛出一个新异常，并且注明错误信息：

![](images/1665568989683-28b02cf7-057e-4dd3-a50d-6572b6c37280-d975d877.png)

然后在异常拦截器对异常进行处理，看下面的代码：

```java
public String intercept(ActionInvocation actioninvocation) {
    String result = null; // Action的返回值  
    try {  
        // 运行被拦截的Action,期间如果发生异常会被catch住  
        result = actioninvocation.invoke();  
        return result;  
    } catch (Exception e) {  
        /** 
    * 处理异常 
    */  
        String errorMsg = "未知错误！";  
        //通过instanceof判断到底是什么异常类型  
        if (e instanceof BaseException) {  
            BaseException be = (BaseException) e;  
            be.printStackTrace(); //开发时打印异常信息，方便调试  
            if(be.getMessage()!=null||Constants.BLANK.equals(be.getMessage().trim())){  
                //获得错误信息  
                errorMsg = be.getMessage().trim();  
            }  
        } else if(e instanceof RuntimeException){  
            //未知的运行时异常  
            RuntimeException re = (RuntimeException)e;  
            re.printStackTrace();  
        } else{  
            //未知的严重异常  
            e.printStackTrace();  
        }  
        //把自定义错误信息  
        HttpServletRequest request = (HttpServletRequest) actioninvocation  
                                      .getInvocationContext().get(StrutsStatics.HTTP_REQUEST);  
    
        /** 
    * 发送错误消息到页面 
    */  
        request.setAttribute("errorMsg", errorMsg);  
    
        /** 
    * log4j记录日志 
    */  
        Log log = LogFactory  
            .getLog(actioninvocation.getAction().getClass());  
        if (e.getCause() != null){  
            log.error(errorMsg, e);  
        }else{  
            log.error(errorMsg, e);  
        }  
    
        return "error";  
    }// ...end of catch  
}
```

需要注意的是:在使用instanceof判断异常类型的时候一定要从子到父依次找，比如BaseException继承与RuntimeException，则必须首先判断是否是BaseException再判断是否是RuntimeException。

最后在error JSP页面显示具体的错误消息即可：

![](images/1665569065341-4a76fdac-32b5-4c4a-a0fb-5cc17d3b4c3b-71ecb7b6.png)

以上异常拦截器可以使用其它很多技术替换：比如spring aop，servlet filter等，根据项目实际情况处理。

![](images/1665569084331-4bb79a63-0a06-46da-88f6-6eef34576516-b1dd78c4.png)

【补充】ajax也可以进行拦截，但是因为ajax属于异步操作，action通过response形式直接把数据返回给ajax回调函数，如果发生异常，ajax是不会执行页面跳转的，所以必须把错误信息返回给回调函数，我针对json数据的ajax是这样做的：

![](images/1665569109038-058bcb8d-a759-4de8-b0d8-326dd84a56b9-7185f81b.png)

来源： [http://blog.csdn.net/luqin1988/article/details/7970988](http://blog.csdn.net/luqin1988/article/details/7970988)
