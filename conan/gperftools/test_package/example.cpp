#include <iostream>

int main() {
    std::cout << "Hello" << std::endl;
    int *p = new int;
    *p = 1;
    delete p;
    return 0;
}
