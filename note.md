# 常用的应用程序测试

## Redis

1. 安装redis(在Ubuntu上安装)

    参考[官方](https://redis.io/docs/getting-started/installation/install-redis-on-linux/)，使用snap安装：

    ```shell
    sudo snap install redis
    ```

    添加环境变量

    ```shell
    echo -e "\n\n# add snap bin" >> ~/.bashrc
    echo -e "export REDIS_BIN=/snap/redis/current/usr/bin" >> ~/.bashrc
    echo -e "export PATH=\"REDIS_BIN:\$PATH\"" >> ~/.bashrc
    source ~/.bashrc
    ```

2. 从源码安装(在risc v架构的服务器上)

   首先[下载](https://download.redis.io/releases/?_gl=1*1y3q869*_ga*NTU2NTk0NDg4LjE2OTQ5NTkyMzE.*_ga_8BKGRQKRPV*MTY5NTAwMTU5NC4zLjEuMTY5NTAwMTkxNy44LjAuMA..)源码。

    ```powershell
    // 将安装包上传
    scp D:\EdgeDownloads\redis-7.2.1.tar.gz riscv-server:~
    ```

    在服务器中

    ```shell
    cd ~/redis-7.2.1
    make
    make test
    make install
    ```

    关于make test报错：You need tcl 8.5 or newer in order to run the Redis test的解决方式：

    ```shell
    sudo apt-get install tcl
    ```

3. 启动redis服务器：

    解决Ubuntu22.04中的libssl.so.1.1文件缺失，参考[这里](https://stackoverflow.com/questions/72133316/libssl-so-1-1-cannot-open-shared-object-file-no-such-file-or-directory)。

    ```shell
    wget http://nz2.archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2.19_amd64.deb

    sudo dpkg -i libssl1.1_1.1.1f-1ubuntu2.19_amd64.deb
    ```

### Redis BenchMark补充说明

参考[官方文档](https://redis.io/docs/management/optimization/benchmarks/#pitfalls-and-misconceptions)

1. redis是单线程服务器，不会利用多核加速

    从命令执行的POV来看，Redis基本上是一个单线程服务器(实际上，Redis的现代版本使用线程来做不同的事情)。它不是为了从多个CPU内核中获益而设计的。人们应该启动几个Redis实例，以便在需要时在几个核心上进行扩展。将单个Redis实例与多线程数据存储进行比较是不公平的。

2. 测试的性能瓶颈可能在客户端而不是服务端

    例如，Redis和memcached在单线程模式下可以比较GET/SET操作。两者都是内存中的数据存储，在协议级别上以相同的方式工作。如果它们各自的基准测试应用程序以相同的方式(流水线)聚合查询，并使用相似数量的连接，那么这种比较实际上是有意义的。

3. 影响redis性能的因素

    **网络是一个直接因素，在运行benchmark之前应该测试一下redis服务器的latency。**

    ```shell
    # 测量客户端和服务器之间的延迟
    timeout 5s redis-cli --latency
    # 测量redis内在的延迟
    redis-cli --intrinsic-latency 100
    ```

    关于更多的latency，参考哲篇[博客](https://blog.netdata.cloud/7-types-of-redis-latency/)

    然后网卡本身的带宽会对redis的benchmark存在显示，引用官方的说明：

    > 在Redis中以100000 q/s的速度设置4 KB字符串的基准测试，实际上会消耗3.2 Gbit/s的带宽，可能适合10 Gbit/s的链路，但不适合1 Gbit/s的链路。在许多现实场景中，Redis的吞吐量在受到CPU限制之前就受到了网络的限制。为了在一台服务器上整合几个高吞吐量的Redis实例，值得考虑将一个10 Gbit/s的网卡或多个1 Gbit/s的网卡与TCP/IP绑定。

    在linux中使用ethtool查看网卡带宽：

    ```shell
    # 先使用ifconfig查看现有的网络适配器，再用ethtool查看对应的适配器
    ethtool eth0
    ```

    在windows中查看网卡带宽：

    ```powershell
    Get-NetAdapter | select interfaceDescription, name, status, linkSpeed
    ```

    **CPU的单核性能对Redis的影响更大**

    可以考虑将进程限制在单个CPU上运行以避免缓存失效导致的性能开销，常用的工具有：cpuset、tuna，参考[这里](https://stackoverflow.com/questions/11111852/how-to-shield-a-cpu-from-the-linux-scheduler-prevent-it-scheduling-threads-onto)。

    其他：
    > tuna运行报错"ValueError: Namespace Gtk not available"的[解决方式](https://stackoverflow.com/questions/56823857/valueerror-namespace-gtk-not-available)。

    **相对于TCP/IP loopback使用unix domain sockets能提高50%的吞吐量**

    但是随着流水线加深而效果降低。

    **其他**

    RAM速度和内存带宽似乎对全局性能不太重要，特别是对于小对象。对于大型对象(>10 KB)，这可能会变得明显，特别是对于小对象。对于大型对象(>10 KB)，这可能会变得明显。

    redis在虚拟机中运行得更慢。

    客户端连接的数量也是一个重要因素

### Redis Latency

> "In this context latency is the maximum delay between the time a client issues a command and the time the reply to the command is received by the client. Usually Redis processing time is extremely low, in the sub microsecond range, but there are certain conditions leading to higher latency figures."

在此上下文中，延迟是客户机发出命令到客户机接收命令回复之间的最大延迟。通常Redis的处理时间非常低，在亚微秒范围内，但在某些情况下会导致更高的延迟数字。

1. intrinsic latency

    运行Redis的环境固有的一部分延迟，这是由操作系统内核或者虚拟化程序提供的延迟。它是redis延迟的baseline，无法被消除，也无法取得比intrinsic latency更低的延迟

2. latency sourcese

    fork、transparent huge pages、swapping、 disk I/O

    禁用透明的transparent huge pages

    ```shell
    echo never > /sys/kernel/mm/transparent_hugepage/enabled
    ```

### Redis性能测试

1. 创建redis的CPU隔离环境并启动redis服务器

    ```shell
    sudo cset shield --cpu=0-3
    sudo cset shield --exec redis-server > redis_server_info.txt 2>&1 &
    ```

2. 测量latency

    ```shell
    sudo cset shield --exec redis-cli -- --latency -i 5 --csv \
    | tail -n +2 > latency.csv
    sudo cset shield --exec redis-cli -- intrinsic-latency 100 --csv \
    | tail -n +2 > intrinsic-latency.csv
    ```

3. 运行benchmark

    ```shell
    sudo cset shield --exec redis-benchmark \
    -- -P 16 -d 32 -c 100 -n 20000 --csv \
    | tail -n +2 > redis-benchmark.csv 
    ```
