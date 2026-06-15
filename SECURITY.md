# Security policy

## This project is intentionally vulnerable

deadwood is a training range built **on purpose** with security flaws — they are
the product, not bugs. Please don't report the flaws in the levels. deadwood binds
to `127.0.0.1` and refuses any other host unless explicitly forced; **never expose
it** to a network, a VM bridge, or the internet.

## Reporting a real vulnerability

If you find a flaw in deadwood *itself* — something that escapes loopback, harms
someone who merely installed it, or runs code outside a level's intended exercise
— report it privately via GitHub Security Advisories ("Report a vulnerability" on
the repository's Security tab), or open a minimal issue if it isn't sensitive.
Include the version (`deadwood --version`) and steps to reproduce.

## Responsible use

Run deadwood only on a machine you control, on loopback. Practising the techniques
it teaches against systems you don't own or aren't authorized to test is illegal.
