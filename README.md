# zh-mxz-list

## TL;DR (我只想屏蔽MXZ，怎么办？)

确保浏览器安装了**用户脚本管理器**，点击[这里](https://github.com/c6h6cl6-code/zh-mxz-list/raw/refs/heads/main/zhbl.user.js)安装用户脚本，导航到[知乎的屏蔽页面](https://www.zhihu.com/settings/filter)后点击**同步黑名单**（没有看到按钮的可以尝试刷新）。在所有弹出的4个对话框中直接选择OK就会自动开始屏蔽，操作完成后会弹出对话框提示，在此之前不要离开页面，可以打开浏览器控制台查看进度。屏蔽的进度自动保存在本地浏览器，如果有多个设备或者浏览器，可以只在一台设备上使用。

## ZHBL 1.0

一个**ZHBL 1.0**阻止列表**文件**由以下内容组成。

这是阻止列表的头部，它包含了 `[ZHBL 1.0]`、标题和代数命名空间（Namespace）：

```ZHBL
[ZHBL 1.0]
! Title: 标题，可随意选择
! Namespace: github.com/c6h6cl6-code/zh-mxz-list.git
! 这是一个注释
```

这是一个**外部阻止列表条目**，用于引用**受信任的**外部阻止列表：

```
i,https://raw.githubusercontent.com/c6h6cl6-code/zh-mxz-list/refs/heads/main/test-include.txt
```

这是一个**阻止列表条目**，包含代数（generation）、知乎用户的 `urlToken`、`id` 和用户昵称：

```ZHBL
u,0,jian-yan-zhe-60,02825cb8023c91115428cf772f2aea2b,全自动代号盒帝
```

虽然 `urlToken` 是阻止用户所需的全部信息，但仍然推荐加入 `id` 和用户昵称，前者可以处理用户修改 `urlToken` 的情况，后者方便维护。

提示：你可以通过 `https://www.zhihu.com/people/<urlToken/id>` 访问这个知乎用户的主页。

## 命名空间和代数
每一个阻止列表都**应该**有对应的**命名空间**（namespace），具有相同命名空间的阻止列表可以被考虑为一个阻止列表。通常情况下，由**同一个开发者维护**且**属于同一类别**的多个阻止列表使用相同的命名空间。

所有**阻止列表条目**都具有一个非唯一的**代数**（generation），它代表一个或者多个条目加入阻止列表的顺序。代数仅在同一命名空间下有意义。

代数的设计是为了避免重复导入阻止列表的同时简化用户需要存储或者记忆的信息。维护者应该尽可能一次性增加多个条目并使用相同的代数，避免膨胀。

## 创建阻止列表，或者贡献MXZ列表

当发现MXZ目标后，在用户主页打开开发者工具，在控制台中粘贴以下内容并回车：

```JavaScript
(() => {
  try {
    // Get urlToken from current URL
    const urlToken = location.pathname.split('/').filter(p => p)[1].split('?')[0];
    if (!urlToken) throw new Error("Cannot extract urlToken from URL.");

    // Get id="js-initialData"
    const rawData = document.querySelector('#js-initialData')?.textContent;
    if (!rawData) throw new Error("Cannot find js-initialData element.");

    const data = JSON.parse(rawData);

    // Extract user object using urlToken
    const userObj = data?.initialState?.entities?.users?.[urlToken];
    if (!userObj) throw new Error(`User object not found for urlToken "${urlToken}".`);

    const userID = userObj.id;
    const name = userObj.name || "(no name)";

    // Print
    console.log(`u,0,${urlToken},${userID},${name}`);
  } catch (e) {
    console.error("Error:", e.message);
  }
})();
```

控制台将会打印类似这样的信息：

```ZHBL
u,0,jian-yan-zhe-60,02825cb8023c91115428cf772f2aea2b,全自动代号盒帝
```

这是一个合法的**ZHBL 1.0**阻止列表**条目**。

也可以[安装](https://raw.githubusercontent.com/c6h6cl6-code/zh-mxz-list/refs/heads/main/zhbl_gen.user.js)用于生成ZHBL条目的用户脚本：`https://raw.githubusercontent.com/c6h6cl6-code/zh-mxz-list/refs/heads/main/zhbl_gen.user.js`

## 贡献

你可以通过Issue或者Pull Request向本项目提交**MXZ**用户，建议将多个用户合并提交加快效率。目前不接受**外部阻止列表条目**的提交。

提示：请务必使用单独的GitHub账号提交，其用户名不应与你的过去和将来可能使用的身份（包括可识别的互联网身份）有联系。
