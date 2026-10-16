/* B站投稿页发布前一键校验（粘贴到浏览器控制台运行）。
 * 按 SKILL.md 里的 placeholder 定位法检查所有必填项，全部通过再点"存草稿"。
 * 有任何一项 FAIL 就先修，不要强行提交。
 */
(function () {
  const out = [];
  const ok = (name, cond, hint) => out.push(`${cond ? "PASS" : "FAIL"}  ${name}${cond ? "" : "  <- " + hint}`);

  const byPh = (ph) => document.querySelector(`[placeholder="${ph}"]`);
  const titleEl = document.querySelector('input[placeholder*="标题"]') ||
                  document.querySelector('.video-title input, input[maxlength="80"]');
  ok("标题已填", titleEl && titleEl.value.trim().length > 0, "标题是空的");

  const desc = byPh("填写更全面的相关信息");
  ok("简介已填", desc && desc.innerText.trim().length > 0, "简介 contenteditable 为空");

  const tags = document.querySelectorAll(".tag-item, .label-item");
  ok("标签≥1个", tags.length >= 1, "一个标签都没加");

  const coverImg = document.querySelector('.cover-preview img, [class*="cover"] img');
  ok("封面已上传", !!coverImg, "封面区域没有图片");

  const moreBtn = [...document.querySelectorAll("div,span")].find(e => e.textContent.trim() === "更多设置");
  const moreOpen = moreBtn && moreBtn.closest("[class]") &&
    !!document.querySelector('[placeholder="有趣的动态描述"]');
  ok("更多设置已展开", !!moreOpen, "先点开展开更多设置");

  const moment = byPh("有趣的动态描述");
  ok("粉丝动态已填", moment && moment.innerText.trim().length > 0, "粉丝动态为空（100字以内写一个钩子）");
  ok("粉丝动态≤100字", !moment || moment.innerText.trim().length <= 100, "超100字会被截断");

  const aiDecl = [...document.querySelectorAll("label,span")].find(e => /AI生成|含AI/.test(e.textContent));
  ok("创作声明含AI生成内容", !!aiDecl, "更多设置里把创作声明选成含AI生成内容");

  console.log(out.join("\n"));
  return out.every(l => l.startsWith("PASS"));
})();
